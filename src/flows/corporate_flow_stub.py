from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from pathlib import Path
import csv, json, time, uuid, re
from src.runtime.config import RunConfig
from src.runtime.budget import BudgetManager, BudgetExceeded
from src.tools.webtools import WebSearch, WebFetch
from src.tools.sheets import SheetsLedger
from src.tools.explorium import ExploriumClient
from src.scoring.corporate import score_corporate


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


def is_aggregator_domain(url: str) -> bool:
    from urllib.parse import urlparse
    parsed = urlparse((url or "").lower())
    if not parsed.hostname:
        return False
    domain = parsed.hostname.replace('www.', '')
    aggregator_domains = {
        'forbes.com','bloomberg.com','reuters.com','newsweek.com','medium.com','hbr.org','linkedin.com','twitter.com',
        'facebook.com','youtube.com','crunchbase.com','gartner.com','g2.com','capterra.com'
    }
    if domain in aggregator_domains:
        return True
    patterns = ['news', 'blog', 'press', 'media', 'review', 'report', 'magazine']
    return any(p in domain for p in patterns)


def is_primary_domain(url: str, org_name: str) -> bool:
    from urllib.parse import urlparse
    parsed = urlparse((url or "").lower())
    if not parsed.hostname:
        return False
    domain = parsed.hostname.replace('www.', '')
    org_lower = (org_name or "").lower()
    org_words = re.findall(r"\w+", org_lower)
    org_words = [w for w in org_words if len(w) > 3]
    return any(w in domain for w in org_words)


def is_listicle_or_directory(title: str, url: str, text: str) -> bool:
    title_l = (title or "").lower()
    url_l = (url or "").lower()
    text_l = (text or "").lower()
    bad_terms = ["top ", "best ", "list of", "directory", "companies", "providers", "ultimate guide", "how to", "roundup"]
    if any(t in title_l for t in bad_terms):
        return True
    if any(t in url_l for t in ["/blog/", "/news/", "/list", "/top-", "/best-"]):
        return True
    if text_l.count("http") > 10 and len(text_l) < 2000:
        return True
    return False


def seed(state: CorporateState) -> CorporateState:
    # Enhanced search queries for corporate academies
    queries = [
        # Direct academy searches
        "corporate academy training program site:linkedin.com",
        "company university employee development",
        "corporate learning center VILT virtual training",
        "employee academy online training program",
        
        # Large enterprise focus
        "Fortune 500 corporate training academy",
        "enterprise learning university program",
        "corporate development center virtual training",
        "global academy employee training program",
        
        # VILT-specific searches
        "corporate academy virtual instructor led training",
        "company university online learning platform",
        "enterprise training center VILT program",
        
        # Award-winning programs
        "Top 125 corporate university training",
        "CLO award corporate academy learning",
        "ATD award corporate learning program"
    ]
    
    all_hits = []
    for q in queries[:8]:  # Limit to prevent budget overrun
        try:
            hits = ws.search(q, max_results=15)
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
        text = (page.get("text") or "")[:20000]
        text_lower = text.lower()
        title = s.get("title", "")
        # Skip low-signal listicles/directories
        if is_listicle_or_directory(title, page.get("url", ""), text):
            continue
        
        # Clean up organization name
        org = title.split(" - ")[0][:120] if title else page["url"]
        if any(word in org.lower() for word in ["ultimate guide", "how to", "corporate training"]):
            from urllib.parse import urlparse
            parsed = urlparse(page["url"])
            if parsed.hostname:
                domain_parts = parsed.hostname.replace('www.', '').split('.')
                if len(domain_parts) > 1 and domain_parts[0] not in ['blog', 'news']:
                    org = domain_parts[0].replace('-', ' ').title()
        
        # Enhanced VILT detection for corporate context
        vilt_indicators = []
        if any(term in text_lower for term in ["virtual instructor led", "vilt", "live online training", "virtual classroom training"]):
            vilt_indicators.append("explicit VILT training")
        if any(term in text_lower for term in ["zoom", "microsoft teams", "webex", "virtual classroom", "adobe connect"]):
            vilt_indicators.append("web conferencing platform")
        if any(term in text_lower for term in ["live webinar", "real-time training", "synchronous learning", "instructor-led online"]):
            vilt_indicators.append("live instruction online")
        if any(term in text_lower for term in ["virtual cohort", "online workshop", "live training session"]):
            vilt_indicators.append("structured virtual programs")
        
        vilt_evidence = "; ".join(vilt_indicators) if vilt_indicators else ""
        
        # Enhanced evidence collection for corporate academies
        evidence = {
            "corporate_org": any(w in text_lower for w in ["corporation", "company", "enterprise", "business", "organization", "firm", "inc", "llc"]),
            "training_program": any(w in text_lower for w in ["academy", "university", "learning center", "development center", "training institute", "education program"]),
            "employee_focus": any(w in text_lower for w in ["employee", "staff", "workforce", "personnel", "team member", "associate", "talent development"]),
            "structured_learning": any(w in text_lower for w in ["curriculum", "learning path", "cohort", "certification program", "skill development", "competency framework"]),
            "large_scale": any(w in text_lower for w in ["global", "worldwide", "enterprise", "fortune", "multinational", "thousands of employees"]),
            "vilt_present": len(vilt_indicators) > 0,
            "external_scope": any(w in text_lower for w in ["partner", "dealer", "supplier", "vendor", "client training", "external"]),
            "awards_recognition": any(w in text_lower for w in ["award", "recognition", "top 125", "clo", "atd", "brandon hall", "excellence"]),
            "evidence_url": page["url"],
            "full_text": text,
            "vilt_evidence": vilt_evidence,
        }
        out.append({"organization": org, "evidence": evidence, "region": state.region})
    state.candidates = out
    return state


def dedupe_enrich_score(state: CorporateState) -> CorporateState:
    ledger = SheetsLedger()
    seen = ledger.load_orgs(segment="corporate")
    outputs = []
    
    # Track regional mix for 80/20 targeting
    na_count = 0
    emea_count = 0
    target_na_ratio = 0.8
    
    for c in state.candidates:
        if len(outputs) >= state.targetcount:
            break
        org_key = (c["organization"] or "").strip().lower()
        if not org_key or org_key in seen:
            continue
            
        # Enrich with Explorium for firmographics and region
        enriched_data = {}
        detected_region = "both"
        
        try:
            budget.assert_can_enrich()
            fx = xl.enrich_firmographics(company=c["organization"])
            budget.tick_enrich()
            if isinstance(fx, dict) and fx:
                enriched_data = fx
                # Check size requirements (min 7500 for corporate)
                if xl.meets_size_requirements(fx, 7500):
                    c["evidence"]["large_scale"] = True
                # Get region from enrichment
                detected_region = xl.get_region(fx)
                c["region"] = detected_region
                # Add enriched data to evidence
                c["evidence"]["enriched_data"] = enriched_data
        except BudgetExceeded:
            pass
        except Exception as e:
            print(f"Enrichment failed for {c['organization']}: {e}")
        
        # Apply regional targeting logic
        if state.region != "both":
            if detected_region != state.region and detected_region != "both":
                continue
        else:
            # Apply 80/20 NA/EMEA mix
            if na_count + emea_count > 0:
                current_na_ratio = na_count / (na_count + emea_count)
                if detected_region == "na" and current_na_ratio > target_na_ratio + 0.1:
                    continue
                elif detected_region == "emea" and current_na_ratio < target_na_ratio - 0.1:
                    continue
            
            if detected_region == "na":
                na_count += 1
            elif detected_region == "emea":
                emea_count += 1
        
        # Use proper corporate scoring with MUST-have enforcement
        sc = score_corporate(c["evidence"])

        # Domain authority validation: Confirmed must be on org primary domain and not aggregator
        evidence_url = c["evidence"]["evidence_url"]
        org_name = c["organization"]
        if sc.tier == "Confirmed":
            if not is_primary_domain(evidence_url, org_name) or is_aggregator_domain(evidence_url):
                sc.tier = "Probable"

        if sc.tier in ["Confirmed", "Probable"]:
            # Add "what to confirm next" for Probable rows
            notes = f"missing={','.join(sc.missing)}" if sc.missing else ""
            if sc.tier == "Probable":
                what_to_confirm = "Locate academy URL on corporate domain (subdomain /academy or /university)"
                if "named_academy" in sc.missing:
                    what_to_confirm = "Find corporate academy/university name on company domain"
                elif "vilt_modality" in sc.missing:
                    what_to_confirm = "Confirm VILT training delivery in academy programs"
                elif "size_requirement" in sc.missing:
                    what_to_confirm = "Verify company size ≥7,500 employees or Fortune status"
                notes = f"{notes}; Next: {what_to_confirm}" if notes else f"Next: {what_to_confirm}"
            
            outputs.append({
                "organization": c["organization"],
                "segment": "corporate",
                "region": c.get("region", detected_region),
                "tier": sc.tier,
                "score": sc.score,
                "evidence_url": c["evidence"]["evidence_url"],
                "notes": notes,
                # Include extracted structured data
                "academy_name": c["evidence"].get("academy_name", ""),
                "academy_url": c["evidence"].get("academy_url", ""),
                "vilt_evidence": c["evidence"].get("vilt_evidence", ""),
                # Add enriched data
                "employee_range": enriched_data.get("employee_range", ""),
                "hq_location": enriched_data.get("hq_location", ""),
                "revenue_range": enriched_data.get("revenue_range", ""),
                "web_conferencing": "Yes" if enriched_data.get("has_video_conferencing") else "",
                "lms": "Yes" if enriched_data.get("has_lms") else "",
                "is_fortune_500": enriched_data.get("is_fortune_500", False),
                "is_global_2000": enriched_data.get("is_global_2000", False),
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

    # Use correct schema from docs/schemas/corporate_headers.txt
    headers_path = Path("docs/schemas/corporate_headers.txt")
    if headers_path.exists():
        headers_line = headers_path.read_text(encoding="utf-8").strip()
        headers = [h.strip() for h in headers_line.split(",") if h.strip()]
    else:
        headers = [
            "Company","HQ_Location","Employee_Count_Range","Revenue_Range","Academy_Name",
            "Academy_URL","Program_Structure","VILT_Evidence","Academy_Scope(Employees/Partners/Dealers)",
            "Web_Conferencing","LMS","Scale_Details","Tier","Confidence","Evidence_URLs","Notes"
        ]

    rows = []
    for o in state.outputs:
        # Determine program structure from evidence
        program_structure = "Cohort-based" if "cohort" in o.get("vilt_evidence", "").lower() else "Self-paced"
        if "certification" in o.get("vilt_evidence", "").lower():
            program_structure += ", Certification Track"
        
        # Determine academy scope
        academy_scope = "Employees"
        if o.get("is_fortune_500") or o.get("is_global_2000"):
            academy_scope += ", Partners"
        
        # Scale details
        scale_details = ""
        if o.get("is_fortune_500"):
            scale_details = "Fortune 500"
        elif o.get("is_global_2000"):
            scale_details = "Global 2000"
        if o.get("employee_range"):
            scale_details += f" ({o.get('employee_range')})" if scale_details else o.get("employee_range")
        
        rows.append({
            "Company": o.get("organization",""),
            "HQ_Location": o.get("hq_location", ""),
            "Employee_Count_Range": o.get("employee_range", ""),
            "Revenue_Range": o.get("revenue_range", ""),
            "Academy_Name": o.get("academy_name", ""),
            "Academy_URL": o.get("academy_url", ""),
            "Program_Structure": program_structure,
            "VILT_Evidence": o.get("vilt_evidence", ""),
            "Academy_Scope(Employees/Partners/Dealers)": academy_scope,
            "Web_Conferencing": o.get("web_conferencing", ""),
            "LMS": o.get("lms", ""),
            "Scale_Details": scale_details,
            "Tier": o.get("tier",""),
            "Confidence": str(o.get("score","")),
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
    na = sum(1 for o in state.outputs if (o.get("region","") or "").lower() == "na")
    emea = sum(1 for o in state.outputs if (o.get("region","") or "").lower() == "emea")
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
