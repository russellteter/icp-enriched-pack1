from dataclasses import dataclass
import re


@dataclass
class ScoreResult:
    score: int
    tier: str
    missing: list[str]


def count_vilt_sessions(text: str) -> int:
    """Count VILT sessions mentioned in text"""
    # Look for session counts in various formats
    session_patterns = [
        r'(\d+)\s+(?:live|virtual|online)\s+sessions?',
        r'(\d+)\s+sessions?\s+(?:per|each|every)\s+(?:month|week)',
        r'(\d+)\s+upcoming\s+(?:sessions?|courses?|classes?)',
        r'(\d+)\s+scheduled\s+(?:sessions?|courses?|classes?)',
    ]
    
    max_count = 0
    for pattern in session_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            for match in matches:
                try:
                    count = int(match)
                    max_count = max(max_count, count)
                except ValueError:
                    continue
    
    return max_count


def extract_vilt_schedule_url(text: str, base_url: str) -> str:
    """Extract VILT schedule URL from text"""
    # Look for schedule/calendar URLs
    schedule_patterns = [
        r'(https?://[^\s]+(?:schedule|calendar|courses|training)[^\s]*)',
        r'(https?://[^\s]+/(?:events|sessions|classes)[^\s]*)',
    ]
    
    for pattern in schedule_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            return matches[0]
    
    # If current page contains schedule indicators, use it
    if any(word in text.lower() for word in ["upcoming sessions", "schedule", "calendar", "register"]):
        return base_url
    
    return ""


def extract_accreditations(text: str) -> str:
    """Extract accreditations from text"""
    accreditation_patterns = [
        r'(PMI|Project Management Institute)',
        r'(NEBOSH)',
        r'(CompTIA)',
        r'(SHRM)',
        r'(ATD)',
        r'(IACET)',
        r'(Six Sigma)',
        r'(PMP)',
        r'(CISSP)',
        r'(ISO \d+)',
    ]
    
    found_accreditations = []
    text_lower = text.lower()
    
    for pattern in accreditation_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found_accreditations.extend(matches)
    
    return "; ".join(found_accreditations) if found_accreditations else ""


def count_instructor_bench(text: str) -> int:
    """Estimate instructor bench size"""
    instructor_patterns = [
        r'(\d+)\s+(?:instructors?|trainers?|facilitators?)',
        r'(?:team|staff)\s+of\s+(\d+)',
        r'(\d+)\s+(?:expert|certified|experienced)\s+(?:instructors?|trainers?)',
    ]
    
    max_count = 0
    for pattern in instructor_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            for match in matches:
                try:
                    count = int(match)
                    max_count = max(max_count, count)
                except ValueError:
                    continue
    
    # If no explicit count, estimate based on descriptive terms
    if max_count == 0:
        if any(term in text.lower() for term in ["large team", "extensive", "numerous"]):
            return 10  # Conservative estimate
        elif any(term in text.lower() for term in ["team of experts", "experienced staff"]):
            return 5
    
    return max_count


def has_red_flags(text: str, url: str) -> bool:
    """Check for red flags that should exclude providers"""
    text_lower = text.lower()
    
    red_flags = [
        # MOOC/marketplace indicators
        "mooc", "coursera", "udemy", "edx", "khan academy",
        # K-12/test prep
        "k-12", "high school", "elementary", "sat prep", "gmat prep",
        # Async-only indicators
        "self-paced only", "no live instruction", "recorded only",
        # Micro bootcamps
        "micro bootcamp", "1-day course", "2-hour session",
        # Consulting-primary
        "consulting services", "advisory only", "strategy consulting"
    ]
    
    for flag in red_flags:
        if flag in text_lower:
            return True
    
    return False


def score_providers(evidence: dict) -> ScoreResult:
    """Score training providers evidence according to ICP definition"""
    score = 0
    missing: list[str] = []

    # Extract additional metrics from evidence
    text = evidence.get("full_text", "")
    url = evidence.get("evidence_url", "")
    
    # Check for red flags first
    if has_red_flags(text, url):
        return ScoreResult(score=0, tier="Excluded", missing=["red_flags_present"])
    
    vilt_sessions_90d = count_vilt_sessions(text)
    vilt_schedule_url = extract_vilt_schedule_url(text, url)
    accreditations = extract_accreditations(text)
    instructor_bench = count_instructor_bench(text)
    
    # Update evidence with extracted fields
    evidence["vilt_sessions_90d"] = vilt_sessions_90d
    evidence["vilt_schedule_url"] = vilt_schedule_url
    evidence["accreditations"] = accreditations
    evidence["instructor_bench"] = instructor_bench

    # B2B focus (20 points, MUST)
    if evidence.get("corporate_focus"):
        score += 20
    else:
        missing.append("b2b_focus")

    # VILT core offering (25 points, MUST)
    if evidence.get("virtual_capability"):
        score += 25
    else:
        missing.append("vilt_core_offering")

    # Public calendar ≥5/90d (20 points, MUST)
    if vilt_schedule_url and vilt_sessions_90d >= 5:
        score += 20
    else:
        missing.append("public_calendar_5plus")

    # Instructor bench ≥5 (15 points, MUST)
    if instructor_bench >= 5:
        score += 15
    else:
        missing.append("instructor_bench_5plus")

    # Accreditations (10 points)
    if accreditations:
        score += 10

    # Enterprise client logos/cases (10 points)
    if any(term in text.lower() for term in ["enterprise clients", "fortune", "case studies", "success stories"]):
        score += 10

    # Geo reach (5 points)
    if any(term in text.lower() for term in ["global", "international", "worldwide", "na and emea"]):
        score += 5

    # MUST-have enforcement: All four MUSTs required for Confirmed
    must_ok = all([
        evidence.get("corporate_focus"),
        evidence.get("virtual_capability"),
        vilt_schedule_url and vilt_sessions_90d >= 5,
        instructor_bench >= 5
    ])

    if must_ok and score >= 90:
        tier = "Confirmed"
    elif score >= 70:
        tier = "Probable"
    else:
        tier = "Needs Confirmation"

    return ScoreResult(score=score, tier=tier, missing=missing)