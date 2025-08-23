from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from src.runtime.config import RunConfig
from src.runtime.budget import BudgetManager, BudgetExceeded
from src.tools.webtools import WebSearch, WebFetch
from src.tools.sheets import SheetsLedger
from src.tools.explorium import ExploriumClient
from src.scoring.healthcare import score_healthcare

class HCState(BaseModel):
    segment: str = "healthcare"
    region: str = "both" # na|emea|both
    targetcount: int = 50
    mode: str = "fast"
    seeds: list[dict] = Field(default_factory=list)
    candidates: list[dict] = Field(default_factory=list)
    outputs: list[dict] = Field(default_factory=list)
    budget_snapshot: dict | None = None
    summary: str | None = None

cfg = RunConfig()
budget = BudgetManager(cfg)
ws = WebSearch(budget, cfg)
wf = WebFetch(budget, cfg)
xl = ExploriumClient()

def seed(state: HCState) -> HCState:
    q = 'Epic go-live training hospital 2024..2026'
    try:
        hits = ws.search(q, max_results=50)
    except BudgetExceeded as e:
        state.summary = f"Seed aborted: {e}"
        return state
    state.seeds = [{"url": h.get("href"), "title":h.get("title","")} for h in hits if "href" in h]
    return state

def harvest(state: HCState) -> HCState:
    out=[]; seen=set()
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
        title = s.get("title","")
        org = title.split(" - ")[0][:120] if title else page["url"]
        evidence = {
          "provider_org": any(w in text for w in ["hospital","health system","nhs","clinic"]),
          "ehr_activity": any(w in text for w in ["epic go-live","cerner go-live","go live","implementation","switch to epic"]),
          "vilt_present": any(w in text for w in ["virtual training","live online training","zoom","microsoft teams","ms teams"]),
          "training_program": any(w in text for w in ["super user","credentialed trainer","command center"]),
          "large_scale": any(w in text for w in ["hospitals","clinics","employees","caregivers"]),
          "evidence_url": page["url"]
        }
        out.append({"organization": org, "evidence": evidence, "region": state.region})
    state.candidates = out
    return state

def dedupe_enrich_score(state: HCState) -> HCState:
    ledger = SheetsLedger()
    seen = ledger.load_orgs(segment="healthcare")
    outputs=[]
    for c in state.candidates:
        if len(outputs) >= state.targetcount:
            break
        org_key = (c["organization"] or "").strip().lower()
        if not org_key or org_key in seen:
            continue
        # Optional enrich under budget
        try:
            budget.assert_can_enrich()
            fx = xl.enrich_firmographics(company=c["organization"])
            budget.tick_enrich()
            if isinstance(fx, dict):
                rng = (fx.get("Number of employees range all sites") or "").strip()
                if rng in ["10001+","5001-10000"]:
                    c["evidence"]["large_scale"] = True
        except BudgetExceeded:
            pass
        except Exception:
            pass
        sc = score_healthcare(c["evidence"])
        if sc.tier in ["Confirmed","Probable"]:
            outputs.append({
              "organization": c["organization"],
              "segment": "healthcare",
              "region": c["region"],
              "tier": sc.tier,
              "score": sc.score,
              "evidence_url": c["evidence"]["evidence_url"],
              "notes": f"missing={','.join(sc.missing)}" if sc.missing else ""
            })
    state.outputs = outputs
    state.budget_snapshot = budget.snapshot()
    return state

def write_outputs(state: HCState) -> HCState:
    ledger = SheetsLedger()
    if state.outputs:
        ledger.upsert(state.outputs)
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
