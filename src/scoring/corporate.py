from dataclasses import dataclass
import re


@dataclass
class ScoreResult:
    score: int
    tier: str
    missing: list[str]


def extract_academy_name(text: str, url: str) -> str:
    """Extract corporate academy name from text"""
    text_lower = text.lower()
    
    # Look for explicit academy names
    academy_patterns = [
        r'(\w+)\s+(?:corporate\s+)?academy',
        r'(\w+)\s+university',
        r'(\w+)\s+learning\s+center',
        r'(\w+)\s+training\s+center',
        r'(\w+)\s+development\s+center',
    ]
    
    for pattern in academy_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            return matches[0].title() + " Academy"
    
    # Try to extract from URL if it contains academy subdomain
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname and 'academy' in parsed.hostname:
        domain_parts = parsed.hostname.split('.')
        for part in domain_parts:
            if part not in ['www', 'academy', 'com', 'org'] and len(part) > 2:
                return part.title() + " Academy"
    
    return ""


def extract_academy_url(text: str, base_url: str) -> str:
    """Extract academy URL from text"""
    # Look for academy-specific URLs in text
    url_patterns = [
        r'(https?://[^\s]+academy[^\s]*)',
        r'(https?://academy\.[^\s]+)',
        r'(https?://[^\s]+/academy[^\s]*)',
        r'(https?://[^\s]+university[^\s]*)',
    ]
    
    for pattern in url_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            return matches[0]
    
    # If current page is on academy subdomain, use it
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    if parsed.hostname and ('academy' in parsed.hostname or 'university' in parsed.hostname):
        return base_url
    
    return ""


def score_corporate(evidence: dict) -> ScoreResult:
    """Score corporate academy evidence according to ICP definition"""
    score = 0
    missing: list[str] = []

    # Extract additional fields from evidence
    text = evidence.get("full_text", "")
    url = evidence.get("evidence_url", "")
    
    academy_name = extract_academy_name(text, url)
    academy_url = extract_academy_url(text, url)
    
    # Update evidence with extracted fields
    evidence["academy_name"] = academy_name
    evidence["academy_url"] = academy_url

    # Named academy/university exists (50 points, MUST)
    if evidence.get("training_program") and academy_name:
        score += 50
    else:
        missing.append("named_academy")

    # Size ≥7,500 / G2K (10 points, MUST)
    if evidence.get("large_scale"):
        score += 10
    else:
        missing.append("size_requirement")

    # Programmatic cohorts/learning paths (15 points)
    if evidence.get("structured_learning"):
        score += 15

    # VILT modality documented (15 points, MUST)
    if evidence.get("vilt_present"):
        score += 15
    else:
        missing.append("vilt_modality")

    # Awards/recognition (5-15 points) - TODO: implement detection
    if any(term in text.lower() for term in ["top 125", "clo", "atd", "award", "recognition"]):
        score += 10

    # External scope (5 points)
    if evidence.get("external_scope"):
        score += 5

    # MUST-have enforcement: All three MUSTs required for Confirmed
    must_ok = all(evidence.get(k) for k in ["training_program", "large_scale", "vilt_present"]) and academy_name

    if must_ok and score >= 90:
        tier = "Confirmed"
    elif score >= 70:
        tier = "Probable"
    else:
        tier = "Needs Confirmation"

    return ScoreResult(score=score, tier=tier, missing=missing)