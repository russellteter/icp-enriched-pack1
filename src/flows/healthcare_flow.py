from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from pathlib import Path
import csv, json, time, uuid
from src.runtime.config import RunConfig
from src.runtime.budget import BudgetManager, BudgetExceeded
from src.tools.webtools import WebSearch, WebFetch
from src.tools.sheets import SheetsLedger
from src.tools.explorium import ExploriumClient
from src.scoring.healthcare import score_healthcare


class HCState(BaseModel):
    segment: str = "healthcare"
    region: str = "both"  # na|emea|both
    targetcount: int = 50
    mode: str = "fast"
    seeds: list[dict] = Field(default_factory=list)
    candidates: list[dict] = Field(default_factory=list)
    outputs: list[dict] = Field(default_factory=list)
    budget_snapshot: dict | None = None
    summary: str | None = None
    artifacts: dict | None = None


cfg = RunConfig()
budget = BudgetManager(cfg)
ws = WebSearch(budget, cfg)
wf = WebFetch(budget, cfg)
xl = ExploriumClient()


def seed(state: HCState) -> HCState:
    # Multiple search queries to get better coverage
    queries = [
        "Epic go-live training hospital 2024..2026",
        "healthcare EHR training virtual learning",
        "hospital Epic Cerner implementation training",
        "healthcare staff training program virtual",
        "medical center EHR go-live training"
    ]
    
    all_hits = []
    for q in queries:
        try:
            hits = ws.search(q, max_results=20)
            all_hits.extend(hits)
        except BudgetExceeded as e:
            state.summary = f"Seed aborted: {e}"
            break
    
    # Remove duplicates and limit
    seen_urls = set()
    unique_hits = []
    for h in all_hits:
        if "href" in h and h["href"] not in seen_urls:
            seen_urls.add(h["href"])
            unique_hits.append(h)
    
    state.seeds = [{"url": h.get("href"), "title": h.get("title", "")} for h in unique_hits[:50]]
    return state


def harvest(state: HCState) -> HCState:
    out = []
    seen = set()
    for s in state.seeds:
        if len(out) >= state.targetcount * 3:
            break
        url = s.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            page = wf.fetch(url)
        except BudgetExceeded as e:
            state.summary = f"Harvest stopped: {e}"
            break
        except Exception:
            continue
        text = (page.get("text") or "")[:20000].lower()
        title = s.get("title", "")
        org = title.split(" - ")[0][:120] if title else page["url"]
        evidence = {
            "provider_org": any(w in text for w in ["hospital", "health system", "nhs", "clinic", "medical center", "healthcare", "health care"]),
            "ehr_activity": any(w in text for w in ["epic go-live", "cerner go-live", "go live", "implementation", "switch to epic", "epic training", "cerner training", "ehr training", "electronic health record", "emr training"]),
            "vilt_present": any(w in text for w in ["virtual training", "live online training", "zoom", "microsoft teams", "ms teams", "webinar", "online training", "virtual learning", "remote training", "digital training"]),
            "training_program": any(w in text for w in ["super user", "credentialed trainer", "command center", "training program", "learning program", "education program", "certification", "workshop", "course"]),
            "large_scale": any(w in text for w in ["hospitals", "clinics", "employees", "caregivers", "staff", "personnel", "facilities", "locations", "sites"]),
            "evidence_url": page["url"],
        }
        out.append({"organization": org, "evidence": evidence, "region": state.region})
    state.candidates = out
    return state


def dedupe_enrich_score(state: HCState) -> HCState:
    ledger = SheetsLedger()
    seen = ledger.load_orgs(segment="healthcare")
    outputs = []
    for c in state.candidates:
        if len(outputs) >= state.targetcount:
            break
        org_key = (c["organization"] or "").strip().lower()
        if not org_key or org_key in seen:
            continue
        try:
            budget.assert_can_enrich()
            fx = xl.enrich_firmographics(company=c["organization"])
            budget.tick_enrich()
            if isinstance(fx, dict):
                rng = (fx.get("Number of employees range all sites") or "").strip()
                if rng in ["10001+", "5001-10000"]:
                    c["evidence"]["large_scale"] = True
        except BudgetExceeded:
            pass
        except Exception:
            pass
        sc = score_healthcare(c["evidence"])
        if sc.tier in ["Confirmed", "Probable"]:
            outputs.append({
                "organization": c["organization"],
                "segment": "healthcare",
                "region": c["region"],
                "tier": sc.tier,
                "score": sc.score,
                "evidence_url": c["evidence"]["evidence_url"],
                "notes": f"missing={','.join(sc.missing)}" if sc.missing else "",
            })
    state.outputs = outputs
    state.budget_snapshot = budget.snapshot()
    return state


def write_outputs(state: HCState) -> HCState:
    ledger = SheetsLedger()
    if state.outputs:
        ledger.upsert(state.outputs)

    run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    out_dir = Path("runs") / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    headers_path = Path("docs/schemas/healthcare_headers.txt")
    if headers_path.exists():
        headers_line = headers_path.read_text(encoding="utf-8").strip()
        headers = [h.strip() for h in headers_line.split(",") if h.strip()]
    else:
        headers = [
            "Organization","Region","Type","Facilities","EHR_Vendor","EHR_Lifecycle_Phase",
            "GoLive_Date","Training_Model","VILT_Evidence","Web_Conferencing","LMS",
            "Tier","Confidence","Evidence_URLs","Notes"
        ]

    rows = []
    for o in state.outputs:
        rows.append({
            "Organization": o.get("organization",""),
            "Region": o.get("region",""),
            "Type": "",
            "Facilities": "",
            "EHR_Vendor": "",
            "EHR_Lifecycle_Phase": "",
            "GoLive_Date": "",
            "Training_Model": "",
            "VILT_Evidence": "",
            "Web_Conferencing": "",
            "LMS": "",
            "Tier": o.get("tier",""),
            "Confidence": o.get("score",""),
            "Evidence_URLs": o.get("evidence_url",""),
            "Notes": o.get("notes",""),
        })

    csv_path = out_dir / "healthcare.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    total = len(rows)
    na = sum(1 for r in rows if (r.get("Region","") or "").lower() == "na")
    emea = sum(1 for r in rows if (r.get("Region","") or "").lower() == "emea")
    mix = {"total": total, "NA": na, "EMEA": emea}

    summary_lines = [
        f"Segment=healthcare total={total} NA={na} EMEA={emea}",
        f"Budget: {json.dumps(state.budget_snapshot or {}, ensure_ascii=False)}",
    ]
    state.summary = state.summary or "\n".join(summary_lines)
    summary_path = out_dir / "summary.txt"
    summary_path.write_text(state.summary, encoding="utf-8")

    latest_dir = Path("runs") / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    (latest_dir / "healthcare.csv").write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    (latest_dir / "summary.txt").write_text(summary_path.read_text(encoding="utf-8"), encoding="utf-8")

    state.artifacts = {"csv": str(csv_path), "summary": str(summary_path), "mix": mix}
    return state


graph = StateGraph(HCState)
graph.add_node("seed", seed)
graph.add_node("harvest", harvest)
graph.add_node("score", dedupe_enrich_score)
graph.add_node("write", write_outputs)
graph.set_entry_point("seed")
graph.add_edge("seed", "harvest")
graph.add_edge("harvest", "score")
graph.add_edge("score", "write")
graph.add_edge("write", END)

app_graph = graph.compile()


