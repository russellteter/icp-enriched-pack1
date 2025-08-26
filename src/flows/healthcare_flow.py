from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from pathlib import Path
import csv, json, time, uuid, re
from src.runtime.config import RunConfig
from src.runtime.budget import BudgetManager, BudgetExceeded
from src.tools.webtools import WebSearch, WebFetch
from src.tools.sheets import SheetsLedger
from src.tools.explorium import ExploriumClient
from src.tools.openai_client import TokenSafeGPTClient
from src.scoring.healthcare import score_healthcare
from src.definitions.icp_definitions import (
    get_icp_definition, extract_organizations_from_text, 
    is_organization_name, validate_against_icp
)


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
gpt = TokenSafeGPTClient(budget)


def extract_ehr_vendor(text: str) -> str:
    """Extract EHR vendor from text"""
    text_lower = text.lower()
    if any(term in text_lower for term in ["epic", "epic systems", "epiccare"]):
        return "Epic"
    elif any(term in text_lower for term in ["cerner", "oracle cerner", "millennium"]):
        return "Cerner"
    elif any(term in text_lower for term in ["allscripts", "sunrise", "meditech"]):
        return "Allscripts" if "allscripts" in text_lower else "Meditech" if "meditech" in text_lower else "Sunrise"
    elif "athenahealth" in text_lower or "athena" in text_lower:
        return "athenahealth"
    elif "veradigm" in text_lower:
        return "Veradigm"
    return ""


def extract_lifecycle_phase(text: str) -> str:
    """Extract EHR lifecycle phase"""
    text_lower = text.lower()
    if any(term in text_lower for term in ["go-live", "go live", "golive", "launch", "activation"]):
        return "Go-Live"
    elif any(term in text_lower for term in ["implementation", "rollout", "deployment", "install"]):
        return "Implementation"
    elif any(term in text_lower for term in ["optimization", "post-live", "post live", "stabilization"]):
        return "Optimization"
    elif any(term in text_lower for term in ["selection", "evaluation", "planning", "preparation"]):
        return "Planning"
    elif any(term in text_lower for term in ["upgrade", "migration", "transition"]):
        return "Upgrade"
    return ""


def extract_training_model(text: str) -> str:
    """Extract training model/approach"""
    text_lower = text.lower()
    if any(term in text_lower for term in ["super user", "superuser", "power user"]):
        return "Super User Model"
    elif any(term in text_lower for term in ["credentialed trainer", "certified trainer", "ct model"]):
        return "Credentialed Trainer"
    elif any(term in text_lower for term in ["command center", "war room", "support center"]):
        return "Command Center"
    elif any(term in text_lower for term in ["train the trainer", "trainer model"]):
        return "Train-the-Trainer"
    elif any(term in text_lower for term in ["peer training", "buddy system"]):
        return "Peer Training"
    return ""


def extract_go_live_date(text: str) -> str:
    """Extract go-live date from text"""
    import re
    text_lower = text.lower()
    
    # Look for date patterns near go-live mentions
    patterns = [
        r'go[\-\s]?live[^.]{0,30}(\d{1,2}/\d{1,2}/\d{2,4})',
        r'go[\-\s]?live[^.]{0,30}(\w+ \d{1,2},? \d{4})',
        r'launch[^.]{0,30}(\d{1,2}/\d{1,2}/\d{2,4})',
        r'launch[^.]{0,30}(\w+ \d{1,2},? \d{4})',
        r'went live[^.]{0,30}(\d{1,2}/\d{1,2}/\d{2,4})',
        r'went live[^.]{0,30}(\w+ \d{1,2},? \d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1).strip()
    
    # Look for quarters/years
    quarter_pattern = r'(q[1-4] \d{4}|[1-4]q \d{4})'
    if "go live" in text_lower or "golive" in text_lower:
        match = re.search(quarter_pattern, text_lower)
        if match:
            return match.group(1).upper()
    
    return ""


def is_aggregator_domain(url: str) -> bool:
    """Check if URL is from news/aggregator site that should not be primary evidence"""
    from urllib.parse import urlparse
    parsed = urlparse(url.lower())
    if not parsed.hostname:
        return False
    
    domain = parsed.hostname.replace('www.', '')
    
    # Known aggregator/news domains
    aggregator_domains = {
        'beckershospitalreview.com',
        'healthcareitnews.com',
        'hcinnovationgroup.com',
        'newsweek.com',
        'forbes.com',
        'bloomberg.com',
        'reuters.com',
        'modernhealthcare.com',
        'fiercehealthcare.com',
        'healthleadersmedia.com'
    }
    
    # Pattern-based detection
    aggregator_patterns = [
        'news', 'blog', 'press', 'media', 'review', 'report', 'magazine',
        'journal', 'times', 'post', 'herald', 'gazette', 'tribune'
    ]
    
    if domain in aggregator_domains:
        return True
    
    for pattern in aggregator_patterns:
        if pattern in domain:
            return True
    
    return False


def is_primary_domain(url: str, org_name: str) -> bool:
    """Check if URL is likely from the organization's primary domain"""
    from urllib.parse import urlparse
    parsed = urlparse(url.lower())
    if not parsed.hostname:
        return False
    
    domain = parsed.hostname.replace('www.', '')
    org_lower = org_name.lower()
    
    # Healthcare-specific domain patterns that indicate primary sources
    healthcare_tlds = ['.org', '.edu', '.gov', '.nhs.uk', '.ca']
    
    # Check if domain contains organization name parts
    org_words = re.findall(r'\w+', org_lower)
    org_words = [w for w in org_words if len(w) > 3 and w not in ['health', 'care', 'medical', 'hospital', 'system']]
    
    for word in org_words:
        if word in domain:
            return True
    
    # Check for healthcare-specific patterns
    if any(tld in domain for tld in healthcare_tlds) and not is_aggregator_domain(url):
        return True
    
    return False


def extract_organization_name(title: str, url: str) -> str:
    """Extract clean organization name from title and URL"""
    if not title:
        return ""
    
    # Clean up common article patterns
    title = title.strip()
    
    # Remove common prefixes from news articles
    prefixes_to_remove = [
        r"^\d+\s+",  # Numbers at start
        r"^(Breaking|News|Update|Report|Study|Analysis):\s*",
        r"^(How|Why|What|When|Where)\s+",
        r"^The\s+(Ultimate|Complete|Best)\s+Guide\s+",
    ]
    
    for prefix_pattern in prefixes_to_remove:
        title = re.sub(prefix_pattern, "", title, flags=re.IGNORECASE)
    
    # Extract organization from common patterns
    # Pattern: "Organization Name | Publication" or "Organization - Service"
    if " | " in title:
        org_part = title.split(" | ")[0].strip()
        # If it looks like an article title, try the second part
        if any(word in org_part.lower() for word in ["report", "study", "announces", "launches", "implements"]):
            parts = title.split(" | ")
            if len(parts) > 1:
                org_part = parts[1].strip()
        title = org_part
    elif " - " in title:
        title = title.split(" - ")[0].strip()
    
    # Remove common suffixes that indicate article type
    suffixes_to_remove = [
        r"\s+(Report|Study|Analysis|Update|News|Press Release)$",
        r"\s+Goes? Live with Epic$",
        r"\s+Implements? \w+$",
        r"\s+Chooses? \w+ EHR$",
    ]
    
    for suffix_pattern in suffixes_to_remove:
        title = re.sub(suffix_pattern, "", title, flags=re.IGNORECASE)
    
    # If still looks like an article title, try to extract from URL
    if len(title) > 100 or any(word in title.lower() for word in ["epic ugm", "newsweek", "ultimate guide"]):
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.hostname:
            domain_parts = parsed.hostname.split('.')
            # Look for organization name in subdomain or domain
            for part in domain_parts:
                if part not in ['www', 'news', 'blog', 'com', 'org', 'net', 'edu'] and len(part) > 3:
                    return part.replace('-', ' ').title()
    
    return title[:120]  # Limit length


def is_listicle_or_directory(title: str, url: str, text: str) -> bool:
    """Heuristically detect listicles/directories that are low-signal for ICP evidence."""
    title_l = (title or "").lower()
    url_l = (url or "").lower()
    text_l = (text or "").lower()
    bad_terms = [
        "top ", "best ", "list of", "directory", "companies", "providers", "ultimate guide", "how to",
        "roundup", "review of", "compare", "comparison"
    ]
    if any(t in title_l for t in bad_terms):
        return True
    if any(t in url_l for t in ["/blog/", "/news/", "/list", "/top-", "/best-"]):
        return True
    # Very short pages with many links are often directories
    if text_l.count("http") > 10 and len(text_l) < 2000:
        return True
    return False

def seed(state: HCState) -> HCState:
    # Enhanced search strategy (simplified for testing)
    queries = [
        # Direct org searches
        "Intermountain Health Epic training",
        "Mayo Clinic Epic implementation",
        "Cleveland Clinic EHR training",
        
        # General discovery searches  
        "Epic go-live training hospital 2024",
        "healthcare EHR training virtual learning",
        "hospital Epic Cerner implementation training",
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
        text = (page.get("text") or "")[:20000]
        text_lower = text.lower()
        title = s.get("title", "")
        # Skip low-signal listicles/directories
        if is_listicle_or_directory(title, page.get("url", ""), text):
            continue
        # Extract organization names from content (NEW APPROACH)
        orgs_from_content = extract_organizations_from_text(text, "healthcare")
        orgs_from_title = [extract_organization_name(title, page["url"])]
        
        # Combine and validate
        candidate_orgs = orgs_from_content + orgs_from_title
        validated_orgs = []
        
        for org_candidate in candidate_orgs:
            if not org_candidate or len(org_candidate) < 3:
                continue
            
            # Use ICP-aware validation
            if is_organization_name(org_candidate, "healthcare"):
                # GPT Enhancement: Canonicalize if needed
                if cfg.max_llm_tokens > 0 and len(org_candidate) > 50:
                    try:
                        gpt_result = gpt.canonicalize_organization_name(org_candidate, page["url"], "healthcare")
                        if gpt_result.get("organization_name") and len(gpt_result["organization_name"]) > 3:
                            print(f"GPT canonicalized: '{org_candidate}' → '{gpt_result['organization_name']}'")
                            validated_orgs.append(gpt_result["organization_name"])
                        else:
                            validated_orgs.append(org_candidate)
                    except (BudgetExceeded, Exception) as e:
                        print(f"GPT canonicalization skipped: {e}")
                        validated_orgs.append(org_candidate)
                else:
                    validated_orgs.append(org_candidate)
        
        # If no valid orgs found from content, skip this page
        if not validated_orgs:
            continue
        
        # Extract structured data
        ehr_vendor = extract_ehr_vendor(text)
        
        # GPT Enhancement: Targeted extraction for missing EHR data
        if cfg.max_llm_tokens > 0 and not ehr_vendor:
            try:
                gpt_extraction = gpt.extract_targeted_data(text[:1000], "healthcare_ehr", "healthcare")
                if gpt_extraction.get("ehr_vendor"):
                    ehr_vendor = gpt_extraction["ehr_vendor"]
                    print(f"GPT extracted EHR vendor: {ehr_vendor}")
            except (BudgetExceeded, Exception) as e:
                print(f"GPT EHR extraction skipped: {e}")
                pass
        lifecycle_phase = extract_lifecycle_phase(text)
        training_model = extract_training_model(text)
        
        # Enhanced VILT detection with specific evidence
        vilt_indicators = []
        if any(term in text_lower for term in ["virtual training", "live online training", "remote training"]):
            vilt_indicators.append("explicit virtual training")
        if any(term in text_lower for term in ["zoom", "microsoft teams", "ms teams", "webex"]):
            vilt_indicators.append("web conferencing tools")
        if any(term in text_lower for term in ["webinar", "online session", "virtual session"]):
            vilt_indicators.append("virtual sessions")
        if any(term in text_lower for term in ["live instructor", "instructor-led", "facilitated online"]):
            vilt_indicators.append("instructor-led online")
        
        vilt_evidence = "; ".join(vilt_indicators) if vilt_indicators else ""
        
        # Create evidence once for the page
        base_evidence = {
            "provider_org": any(w in text_lower for w in ["hospital", "health system", "nhs", "clinic", "medical center", "healthcare", "health care"]),
            "ehr_activity": any(w in text_lower for w in ["epic go-live", "cerner go-live", "go live", "implementation", "switch to epic", "epic training", "cerner training", "ehr training", "electronic health record", "emr training"]),
            "vilt_present": len(vilt_indicators) > 0,
            "training_program": any(w in text_lower for w in ["super user", "credentialed trainer", "command center", "training program", "learning program", "education program", "certification", "workshop", "course"]),
            "large_scale": any(w in text_lower for w in ["hospitals", "clinics", "employees", "caregivers", "staff", "personnel", "facilities", "locations", "sites"]),
            "evidence_url": page["url"],
            # New structured fields
            "ehr_vendor": ehr_vendor,
            "lifecycle_phase": lifecycle_phase,
            "training_model": training_model,
            "vilt_evidence": vilt_evidence,
            "full_text": text,
        }
        
        # Create separate entry for each validated organization found
        for org in validated_orgs:
            print(f"Found healthcare organization: {org}")
            out.append({"organization": org, "evidence": base_evidence.copy(), "region": state.region})
    state.candidates = out
    return state


def dedupe_enrich_score(state: HCState) -> HCState:
    ledger = SheetsLedger()
    seen = ledger.load_orgs(segment="healthcare")
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
        
        # Enhanced validation using ICP definitions
        if not is_organization_name(c["organization"], "healthcare"):
            print(f"Filtered non-organization: {c['organization']}")
            continue
            
        # Additional validation against ICP criteria
        validation_result = validate_against_icp(c, "healthcare")
        if not validation_result.get("valid", True):
            print(f"ICP validation failed for {c['organization']}: {validation_result.get('reason')}")
            continue
            
        # Enrich with Explorium for firmographics and region
        enriched_data = {}
        detected_region = "both"  # default
        
        try:
            budget.assert_can_enrich()
            fx = xl.enrich_firmographics(company=c["organization"])
            budget.tick_enrich()
            if isinstance(fx, dict) and fx:
                enriched_data = fx
                # Check size requirements (min 5000 for healthcare)
                if xl.meets_size_requirements(fx, 5000):
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
            pass
        
        # Apply regional targeting logic
        if state.region != "both":
            # Filter by requested region
            if detected_region != state.region and detected_region != "both":
                continue
        else:
            # Apply 80/20 NA/EMEA mix
            if na_count + emea_count > 0:
                current_na_ratio = na_count / (na_count + emea_count)
                if detected_region == "na" and current_na_ratio > target_na_ratio + 0.1:
                    continue  # Skip, we have too many NA
                elif detected_region == "emea" and current_na_ratio < target_na_ratio - 0.1:
                    continue  # Skip, we have too many EMEA
            
            # Update counts
            if detected_region == "na":
                na_count += 1
            elif detected_region == "emea":
                emea_count += 1
        
        sc = score_healthcare(c["evidence"])
        
        # GPT Enhancement: Evidence adjudication for borderline cases
        evidence_url = c["evidence"]["evidence_url"]
        org_name = c["organization"]
        
        if cfg.max_llm_tokens > 0 and sc.tier in ["Probable", "Confirmed"] and is_primary_domain(evidence_url, org_name):
            try:
                # Only adjudicate on provider/corporate domains per PRD
                gpt_adjudication = gpt.adjudicate_evidence(
                    (c["evidence"].get("full_text", ""))[:800], 
                    evidence_url, 
                    "healthcare", 
                    sc.missing
                )
                
                # If GPT says must-haves are NOT met, downgrade to Probable
                if not gpt_adjudication.get("meets_must_haves", False) and sc.tier == "Confirmed":
                    sc.tier = "Probable"
                    print(f"GPT downgraded {org_name} from Confirmed to Probable")
                    
                # Add GPT's what_to_confirm_next
                if sc.tier == "Probable" and gpt_adjudication.get("what_to_confirm_next"):
                    gpt_next_step = gpt_adjudication["what_to_confirm_next"]
                    
            except (BudgetExceeded, Exception) as e:
                print(f"GPT adjudication skipped for {org_name}: {e}")
        
        # Apply domain authority validation: Confirmed must be on org primary domain
        if sc.tier == "Confirmed":
            if not is_primary_domain(evidence_url, org_name):
                sc.tier = "Probable"
                additional_notes = "primary-domain evidence required for Confirmed"
                if sc.missing:
                    sc.missing.append(additional_notes)
                else:
                    sc.missing = [additional_notes]
            elif is_aggregator_domain(evidence_url):
                sc.tier = "Probable"
                additional_notes = "aggregator-only evidence"
                if sc.missing:
                    sc.missing.append(additional_notes)
                else:
                    sc.missing = [additional_notes]
        
        if sc.tier in ["Confirmed", "Probable"]:
            # Add "what to confirm next" for Probable rows
            notes = f"missing={','.join(sc.missing)}" if sc.missing else ""
            if sc.tier == "Probable":
                # Use GPT-generated next steps if available, otherwise fallback
                what_to_confirm = ""
                if cfg.max_llm_tokens > 0:
                    try:
                        what_to_confirm = gpt.generate_next_steps(sc.tier, sc.missing, "healthcare")
                    except (BudgetExceeded, Exception):
                        pass
                
                # Fallback to rule-based next steps
                if not what_to_confirm:
                    what_to_confirm = "Find VILT page on provider domain with explicit 'Epic training/THRIVE' reference"
                    if "vilt_present" in sc.missing:
                        what_to_confirm = "Locate virtual training or VILT program on provider domain"
                    elif "ehr_lifecycle" in sc.missing:
                        what_to_confirm = "Confirm active EHR implementation/optimization phase"
                
                notes = f"{notes}; Next: {what_to_confirm}" if notes else f"Next: {what_to_confirm}"
            
            # Extract go-live date from full_text if present
            go_live = ""
            try:
                go_live = extract_go_live_date(c["evidence"].get("full_text", ""))
            except Exception:
                go_live = ""

            outputs.append({
                "organization": c["organization"],
                "segment": "healthcare",
                "region": (c.get("region", detected_region) or "NA").upper(),
                "tier": sc.tier,
                "score": sc.score,
                "evidence_url": evidence_url,
                "notes": notes,
                # Include extracted structured data
                "ehr_vendor": c["evidence"].get("ehr_vendor", ""),
                "lifecycle_phase": c["evidence"].get("lifecycle_phase", ""),
                "training_model": c["evidence"].get("training_model", ""),
                "vilt_evidence": c["evidence"].get("vilt_evidence", ""),
                "go_live_date": go_live,
                # Add enriched data
                "facilities": enriched_data.get("number_of_locations", ""),
                "employee_range": enriched_data.get("employee_range", ""),
                "web_conferencing": "Yes" if enriched_data.get("has_video_conferencing") else "",
                "lms": "Yes" if enriched_data.get("has_lms") else "",
                "hq_location": enriched_data.get("hq_location", ""),
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
        # Determine provider type based on evidence and organization name
        provider_type = "Healthcare Provider"
        org_lower = o.get("organization", "").lower()
        if "hospital" in org_lower or "medical center" in org_lower:
            provider_type = "Hospital System"
        elif "clinic" in org_lower:
            provider_type = "Clinic Network"
        elif "health system" in org_lower or "healthcare system" in org_lower:
            provider_type = "Health System"
        elif "medical group" in org_lower:
            provider_type = "Medical Group"
        
        rows.append({
            "Organization": o.get("organization",""),
            "Region": o.get("region","").upper() if o.get("region") else "BOTH",
            "Type": provider_type,
            "Facilities": str(o.get("facilities", "")) if o.get("facilities") else "",
            "EHR_Vendor": o.get("ehr_vendor", ""),
            "EHR_Lifecycle_Phase": o.get("lifecycle_phase", ""),
            "GoLive_Date": o.get("go_live_date", ""),
            "Training_Model": o.get("training_model", "") or "Super User/Train-the-Trainer",
            "VILT_Evidence": o.get("vilt_evidence", ""),
            "Web_Conferencing": o.get("web_conferencing", ""),
            "LMS": o.get("lms", ""),
            "Tier": o.get("tier",""),
            "Confidence": str(o.get("score","")),
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


