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

    # RESTORED: Proper MUST-have enforcement for healthcare ICP
    # Both EHR activity and VILT presence are required for Tier 1
    must_ok = all(evidence.get(k) for k in ["ehr_activity", "vilt_present"])

    if must_ok and score >= 90:  # Restored proper threshold
        tier = "Tier 1"
    elif score >= 70:  # Restored proper threshold
        tier = "Tier 2"
    else:
        tier = "Tier 3"

    return ScoreResult(score=score, tier=tier, missing=missing)


