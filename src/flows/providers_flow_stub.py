from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from pathlib import Path
import csv, json, time, uuid
from src.runtime.config import RunConfig
from src.runtime.budget import BudgetManager, BudgetExceeded
from src.tools.webtools import WebSearch, WebFetch
from src.tools.sheets import SheetsLedger
from src.tools.explorium import ExploriumClient
from src.scoring.providers import score_providers


class ProvidersState(BaseModel):
    segment: str = "providers"
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
    import re as _re
    org_words = _re.findall(r"\w+", org_lower)
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

def seed(state: ProvidersState) -> ProvidersState:
    # Enhanced search queries for professional training providers
    queries = [
        # VILT-focused searches
        "virtual instructor led training provider VILT",
        "live online training company enterprise",
        "virtual classroom training provider B2B",
        "instructor led online training services",
        
        # Professional/B2B focus
        "professional training provider corporate clients",
        "business training company live virtual",
        "enterprise training provider VILT services",
        "corporate learning provider virtual training",
        
        # Accreditation-focused
        "PMI authorized training provider virtual",
        "NEBOSH virtual training provider",
        "certified training provider VILT delivery",
        "accredited training company virtual classroom",
        
        # Schedule/calendar indicators
        "training provider public schedule virtual sessions",
        "VILT training calendar upcoming sessions",
        "virtual training provider course schedule"
    ]
    
    all_hits = []
    for q in queries[:10]:  # Limit to prevent budget overrun
        try:
            hits = ws.search(q, max_results=12)
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


def harvest(state: ProvidersState) -> ProvidersState:
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
        
        # Clean up organization name - avoid generic titles
        org = title.split(" - ")[0][:120] if title else page["url"]
        if any(word in org.lower() for word in ["top ", "best ", "how to", "ultimate guide", "corporate training companies"]):
            from urllib.parse import urlparse
            parsed = urlparse(page["url"])
            if parsed.hostname:
                domain_parts = parsed.hostname.replace('www.', '').split('.')
                if len(domain_parts) > 1 and domain_parts[0] not in ['blog', 'news', 'list']:
                    org = domain_parts[0].replace('-', ' ').title()
        
        # Enhanced B2B detection for professional training providers
        b2b_indicators = [
            "corporate training", "business training", "enterprise training",
            "professional development", "workforce development", "organizational training",
            "corporate clients", "business clients", "enterprise customers",
            "B2B training", "for organizations", "for companies",
            "workplace training", "employee development", "staff training"
        ]
        
        b2b_score = sum(1 for indicator in b2b_indicators if indicator in text_lower)
        corporate_focus = b2b_score >= 2
        
        # Enhanced VILT detection with specific evidence
        vilt_indicators = []
        if any(term in text_lower for term in ["vilt", "virtual instructor led", "live online training", "real-time training"]):
            vilt_indicators.append("explicit VILT delivery")
        if any(term in text_lower for term in ["virtual classroom", "online classroom", "live virtual session"]):
            vilt_indicators.append("virtual classroom capability")
        if any(term in text_lower for term in ["zoom", "microsoft teams", "webex", "adobe connect", "gotomeeting"]):
            vilt_indicators.append("web conferencing platforms")
        if any(term in text_lower for term in ["live webinar", "interactive session", "real-time interaction"]):
            vilt_indicators.append("live interactive training")
        if any(term in text_lower for term in ["instructor led online", "facilitator led virtual", "trainer led remote"]):
            vilt_indicators.append("instructor-led virtual delivery")
        
        # Public calendar/schedule detection
        schedule_indicators = [
            "upcoming sessions", "training schedule", "course calendar", "public schedule",
            "register now", "available dates", "next session", "training calendar",
            "session dates", "course dates", "workshop dates"
        ]
        has_public_schedule = any(indicator in text_lower for indicator in schedule_indicators)
        
        # Enterprise client detection
        enterprise_indicators = [
            "fortune 500", "fortune 1000", "global 2000", "enterprise clients",
            "corporate clients", "multinational", "large organizations",
            "case studies", "success stories", "client testimonials"
        ]
        has_enterprise_clients = any(indicator in text_lower for indicator in enterprise_indicators)
        
        # Accreditation detection
        accreditation_patterns = ["pmi", "nebosh", "comptia", "shrm", "atd", "iacet", "six sigma", "pmp", "cissp"]
        has_accreditations = any(pattern in text_lower for pattern in accreditation_patterns)
        
        evidence = {
            "training_provider": any(w in text_lower for w in ["training provider", "training company", "learning provider", "education provider", "training organization"]),
            "corporate_focus": corporate_focus,
            "b2b_evidence": b2b_score,
            "service_offering": any(w in text_lower for w in ["training programs", "learning solutions", "professional development", "workshops", "seminars", "courses", "certifications"]),
            "virtual_capability": len(vilt_indicators) >= 2,  # Require strong VILT evidence
            "public_schedule": has_public_schedule,
            "enterprise_clients": has_enterprise_clients,
            "accreditations_present": has_accreditations,
            "instructor_focus": any(w in text_lower for w in ["expert instructors", "certified trainers", "experienced facilitators", "subject matter experts"]),
            "evidence_url": page["url"],
            "full_text": text,
            "vilt_evidence": "; ".join(vilt_indicators) if vilt_indicators else "",
        }
        out.append({"organization": org, "evidence": evidence, "region": state.region})
    state.candidates = out
    return state


def dedupe_enrich_score(state: ProvidersState) -> ProvidersState:
    ledger = SheetsLedger()
    seen = ledger.load_orgs(segment="providers")
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
                # Check size requirements (min 50 for providers)
                if xl.meets_size_requirements(fx, 50):
                    c["evidence"]["adequate_size"] = True
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
        
        # Use proper providers scoring with MUST-have enforcement
        sc = score_providers(c["evidence"])
        
        # Skip excluded providers (red flags)
        if sc.tier == "Excluded":
            continue
        
        # Domain authority validation
        evidence_url = c["evidence"]["evidence_url"]
        org_name = c["organization"]
        if sc.tier == "Confirmed":
            if not is_primary_domain(evidence_url, org_name) or is_aggregator_domain(evidence_url):
                sc.tier = "Probable"
        
        if sc.tier in ["Confirmed", "Probable"]:
            # Add "what to confirm next" for Probable rows
            notes = f"missing={','.join(sc.missing)}" if sc.missing else ""
            if sc.tier == "Probable":
                what_to_confirm = "Locate public calendar URL and count next 90 days; confirm instructor page lists ≥5 trainers"
                if "b2b_focus" in sc.missing:
                    what_to_confirm = "Confirm B2B corporate training focus vs consumer/individual training"
                elif "vilt_core_offering" in sc.missing:
                    what_to_confirm = "Verify live virtual instructor-led training as core service offering"
                elif "public_calendar_5plus" in sc.missing:
                    what_to_confirm = "Find public training schedule with ≥5 sessions in next 90 days"
                elif "instructor_bench_5plus" in sc.missing:
                    what_to_confirm = "Locate instructor/trainer team page showing ≥5 qualified instructors"
                notes = f"{notes}; Next: {what_to_confirm}" if notes else f"Next: {what_to_confirm}"
            
            outputs.append({
                "organization": c["organization"],
                "segment": "providers",
                "region": c.get("region", detected_region),
                "tier": sc.tier,
                "score": sc.score,
                "evidence_url": c["evidence"]["evidence_url"],
                "notes": notes,
                # Include extracted structured data
                "vilt_sessions_90d": c["evidence"].get("vilt_sessions_90d", 0),
                "vilt_schedule_url": c["evidence"].get("vilt_schedule_url", ""),
                "accreditations": c["evidence"].get("accreditations", ""),
                "instructor_bench": c["evidence"].get("instructor_bench", 0),
                "vilt_evidence": c["evidence"].get("vilt_evidence", ""),
                "corporate_focus": c["evidence"].get("corporate_focus", False),
                "vilt_capability": c["evidence"].get("virtual_capability", False),
                # Add enriched data
                "website": enriched_data.get("website", ""),
                "hq_country": enriched_data.get("headquarters_country", ""),
                "industry": enriched_data.get("industry", ""),
                "web_conferencing": "Yes" if enriched_data.get("has_video_conferencing") else "",
                "lms": "Yes" if enriched_data.get("has_lms") else "",
                "enterprise_clients": c["evidence"].get("enterprise_clients", False),
            })
    state.outputs = outputs
    state.budget_snapshot = budget.snapshot()
    return state


def write_outputs(state: ProvidersState) -> ProvidersState:
    ledger = SheetsLedger()
    if state.outputs:
        ledger.upsert(state.outputs)

    run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    out_dir = Path("runs") / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use correct schema from docs/schemas/providers_headers.txt
    headers_path = Path("docs/schemas/providers_headers.txt")
    if headers_path.exists():
        headers_line = headers_path.read_text(encoding="utf-8").strip()
        headers = [h.strip() for h in headers_line.split(",") if h.strip()]
    else:
        headers = [
            "Company","Website","HQ_Country","Regions_Served(NA/EMEA/Both)","Provider_Type","Primary_Tags",
            "B2B_Evidence_URL","VILT_Modality_URL","Web_Conferencing","LMS","VILT_Sessions_90d",
            "VILT_Schedule_URL","Instructor_Bench_Notes","Accreditations","Named_Enterprise_Customers(Y/N)",
            "Named_Enterprise_Examples","Tier","Confidence","Evidence_URLs","Notes"
        ]

    rows = []
    for o in state.outputs:
        # Determine provider type based on evidence
        provider_type = "B2B Training Provider"
        if o.get("accreditations"):
            provider_type = "Accredited Training Provider"
        
        # Extract website domain
        website = o.get("website", "")
        if not website and o.get("evidence_url"):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(o.get("evidence_url"))
                website = parsed.hostname or ""
            except:
                website = ""
        
        # Primary tags based on evidence
        tags = ["Corporate Training"]
        if o.get("accreditations"):
            tags.append("Accredited")
        if "virtual" in o.get("vilt_evidence", "").lower():
            tags.append("VILT Specialist")
        if o.get("enterprise_clients"):
            tags.append("Enterprise Clients")
        
        # Regions served
        regions_served = o.get("region", "Both").upper()
        if regions_served == "BOTH":
            regions_served = "Both"
        
        rows.append({
            "Company": o.get("organization",""),
            "Website": website,
            "HQ_Country": o.get("hq_country", ""),
            "Regions_Served(NA/EMEA/Both)": regions_served,
            "Provider_Type": provider_type,
            "Primary_Tags": ", ".join(tags),
            "B2B_Evidence_URL": o.get("evidence_url", "") if o.get("corporate_focus") else "",
            "VILT_Modality_URL": o.get("evidence_url", "") if o.get("vilt_capability") else "",
            "Web_Conferencing": o.get("web_conferencing", ""),
            "LMS": o.get("lms", ""),
            "VILT_Sessions_90d": str(o.get("vilt_sessions_90d", 0)),
            "VILT_Schedule_URL": o.get("vilt_schedule_url", ""),
            "Instructor_Bench_Notes": f"Est. {o.get('instructor_bench', 0)} instructors" if o.get("instructor_bench") else "",
            "Accreditations": o.get("accreditations", ""),
            "Named_Enterprise_Customers(Y/N)": "Y" if o.get("enterprise_clients") else "N",
            "Named_Enterprise_Examples": "",  # Could be extracted with GPT in Phase 4
            "Tier": o.get("tier",""),
            "Confidence": str(o.get("score","")),
            "Evidence_URLs": o.get("evidence_url",""),
            "Notes": o.get("notes",""),
        })

    csv_path = out_dir / "providers.csv"
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
        f"Segment=providers total={total} NA={na} EMEA={emea}",
        f"Budget: {json.dumps(state.budget_snapshot or {}, ensure_ascii=False)}",
    ]
    state.summary = state.summary or "\n".join(summary_lines)
    summary_path = out_dir / "summary.txt"
    summary_path.write_text(state.summary, encoding="utf-8")

    latest_dir = Path("runs") / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    (latest_dir / "providers.csv").write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    (latest_dir / "summary.txt").write_text(summary_path.read_text(encoding="utf-8"), encoding="utf-8")

    state.artifacts = {
        "csv_path": str(csv_path),
        "summary_path": str(summary_path),
        "mix": mix
    }
    return state


# Create the workflow graph
app_graph = StateGraph(ProvidersState)

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
