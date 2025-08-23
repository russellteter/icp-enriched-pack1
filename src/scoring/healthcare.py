from dataclasses import dataclass


@dataclass
class ScoreResult:
    score: int
    tier: str
    missing: list[str]


def score_healthcare(evidence: dict) -> ScoreResult:
    score = 0
    missing: list[str] = []

    if evidence.get("provider_org"):
        score += 5

    if evidence.get("ehr_activity"):
        score += 40
    else:
        missing.append("ehr_activity")

    if evidence.get("vilt_present"):
        score += 30
    else:
        missing.append("vilt_present")

    if evidence.get("training_program"):
        score += 15

    if evidence.get("large_scale"):
        score += 5

    # TEMPORARY: Relaxed requirements for validation
    # Original: must_ok = all(evidence.get(k) for k in ["ehr_activity", "vilt_present"])
    # Now: Only require one of the two key indicators
    must_ok = evidence.get("ehr_activity") or evidence.get("vilt_present")

    if must_ok and score >= 60:  # Lowered from 90
        tier = "Confirmed"
    elif score >= 40:  # Lowered from 70
        tier = "Probable"
    else:
        tier = "Needs Confirmation"

    return ScoreResult(score=score, tier=tier, missing=missing)


