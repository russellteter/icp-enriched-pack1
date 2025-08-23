from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from pathlib import Path
import csv, json, time, uuid
from src.runtime.config import RunConfig
from src.runtime.budget import BudgetManager, BudgetExceeded
from src.tools.webtools import WebSearch, WebFetch
from src.tools.sheets import SheetsLedger
from src.tools.explorium import ExploriumClient


class CorporateState(BaseModel):
    segment: str = "corporate"
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


def seed(state: CorporateState) -> CorporateState:
    queries = [
        "corporate academy training program",
        "employee development program corporate",
        "corporate learning center training",
        "company academy employee training",
        "corporate university training program"
    ]
    
    all_hits = []
    for q in queries:
        try:
            hits = ws.search(q, max_results=20)
            all_hits.extend(hits)
        except BudgetExceeded as e:
            state.summary = f"Seed aborted: {e}"
            break
    
    seen_urls = set()
    unique_hits = []
    for h in all_hits:
        if "href" in h and h["href"] not in seen_urls:
            seen_urls.add(h["href"])
            unique_hits.append(h)
    
    state.seeds = [{"url": h.get("href"), "title": h.get("title", "")} for h in unique_hits[:50]]
    return state


def harvest(state: CorporateState) -> CorporateState:
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
            "corporate_org": any(w in text for w in ["corporation", "company", "enterprise", "business", "organization", "firm"]),
            "training_program": any(w in text for w in ["training program", "learning program", "development program", "academy", "university", "education program"]),
            "employee_focus": any(w in text for w in ["employee", "staff", "workforce", "personnel", "team member", "associate"]),
            "structured_learning": any(w in text for w in ["curriculum", "course", "workshop", "seminar", "certification", "skill development"]),
            "large_scale": any(w in text for w in ["employees", "staff", "workforce", "personnel", "locations", "sites", "departments"]),
            "evidence_url": page["url"],
        }
        out.append({"organization": org, "evidence": evidence, "region": state.region})
    state.candidates = out
    return state


def dedupe_enrich_score(state: CorporateState) -> CorporateState:
    ledger = SheetsLedger()
    seen = ledger.load_orgs(segment="corporate")
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
        
        # Simple scoring for corporate academies
        score = 0
        missing = []
        
        if c["evidence"].get("corporate_org"):
            score += 20
        if c["evidence"].get("training_program"):
            score += 40
        else:
            missing.append("training_program")
        if c["evidence"].get("employee_focus"):
            score += 20
        if c["evidence"].get("structured_learning"):
            score += 15
        if c["evidence"].get("large_scale"):
            score += 5
        
        if score >= 60:
            tier = "Confirmed"
        elif score >= 40:
            tier = "Probable"
        else:
            tier = "Needs Confirmation"
        
        if tier in ["Confirmed", "Probable"]:
            outputs.append({
                "organization": c["organization"],
                "segment": "corporate",
                "region": c["region"],
                "tier": tier,
                "score": score,
                "evidence_url": c["evidence"]["evidence_url"],
                "notes": f"missing={','.join(missing)}" if missing else "",
            })
    state.outputs = outputs
    state.budget_snapshot = budget.snapshot()
    return state


def write_outputs(state: CorporateState) -> CorporateState:
    ledger = SheetsLedger()
    if state.outputs:
        ledger.upsert(state.outputs)

    run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    out_dir = Path("runs") / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    headers = [
        "Organization","Region","Type","Training_Program","Employee_Focus","Structured_Learning",
        "Large_Scale","Tier","Confidence","Evidence_URLs","Notes"
    ]

    rows = []
    for o in state.outputs:
        rows.append({
            "Organization": o.get("organization",""),
            "Region": o.get("region",""),
            "Type": "Corporate Academy",
            "Training_Program": "",
            "Employee_Focus": "",
            "Structured_Learning": "",
            "Large_Scale": "",
            "Tier": o.get("tier",""),
            "Confidence": o.get("score",""),
            "Evidence_URLs": o.get("evidence_url",""),
            "Notes": o.get("notes",""),
        })

    csv_path = out_dir / "corporate.csv"
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
        f"Segment=corporate total={total} NA={na} EMEA={emea}",
        f"Budget: {json.dumps(state.budget_snapshot or {}, ensure_ascii=False)}",
    ]
    state.summary = state.summary or "\n".join(summary_lines)
    summary_path = out_dir / "summary.txt"
    summary_path.write_text(state.summary, encoding="utf-8")

    latest_dir = Path("runs") / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    (latest_dir / "corporate.csv").write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    (latest_dir / "summary.txt").write_text(summary_path.read_text(encoding="utf-8"), encoding="utf-8")

    state.artifacts = {
        "csv_path": str(csv_path),
        "summary_path": str(summary_path),
        "mix": mix
    }
    return state


# Create the workflow graph
app_graph = StateGraph(CorporateState)

app_graph.add_node("seed", seed)
app_graph.add_node("harvest", harvest)
app_graph.add_node("dedupe_enrich_score", dedupe_enrich_score)
app_graph.add_node("write_outputs", write_outputs)

app_graph.set_entry_point("seed")
app_graph.add_edge("seed", "harvest")
app_graph.add_edge("harvest", "dedupe_enrich_score")
app_graph.add_edge("dedupe_enrich_score", "write_outputs")
app_graph.add_edge("write_outputs", END)

app = app_graph.compile()
