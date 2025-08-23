# Evals Plan

## Datasets
- `icp_eval_set_v1.csv` (20 golds) → expand to 50 in V1.1.
- Structure: eval_id, segment, organization, region_or_hq, expected_tier, required_signals, required_urls, notes.

## Evaluators (local)
1) `schema_completeness`: asserts all required columns for the segment are present and non-empty (org + segment-unique fields).
2) `evidence_support`: fetches each Evidence_URL and checks for supporting phrases (regex library per ICP).
3) `tier_mapping`: recompute score from recorded signals and assert tier mapping.

## Thresholds
- Schema: 100%
- Tier mapping: 100%
- Evidence support: ≥90%

## Process
- Every PR: run local evals (`make eval`) → block on fail.
- Before V1.1: port to LangSmith Align Evals; snapshot baseline; compare on each change.
