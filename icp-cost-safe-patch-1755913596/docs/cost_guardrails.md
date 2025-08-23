# Cost & Usage Guardrails (Token/Context-Safe Architecture)

## Goals
- Avoid hitting model context/usage limits.
- Minimize redundant network & API calls.
- Guarantee runs stop *before* budgets blow up.
- Support multi-hundred discovery by **batching** with resume.

## Design
1. **LLM-lean loops by default**
   - v1 uses **heuristics** (no LLM calls) for harvest/extract/score.
   - Only borderline cases call a model in v1.1+ (guarded by a *token budget*).

2. **Budgets (hard limits)**
   - Per run: `max_searches`, `max_fetches`, `max_enrich_calls`, `max_llm_tokens`.
   - Mode presets: `fast` (tight) vs `deep` (looser) vs `strict` (debug).
   - If exceeded: abort gracefully and write partial outputs + a TXT summary.

3. **Caching & de-dup**
   - Disk cache keyed by URL with a TTL (default 7 days).
   - Per-run URL set to skip duplicates.
   - Domain **allow-list** and per-domain fetch ceilings.

4. **Rate limiting**
   - Conservative per-minute limits for web fetch and enrichment APIs.
   - Jittered exponential backoff on transient failures.

5. **Batching & resume**
   - Process in batches (e.g., 100 candidates at a time).
   - Write checkpoint `runs/<run_id>/state.json` so you can resume.

## Environment & Config (see `.env` or `src/runtime/config.py`)
- `BUDGET_MAX_SEARCHES` (default 120)
- `BUDGET_MAX_FETCHES` (default 150)
- `BUDGET_MAX_ENRICH` (default 80)
- `BUDGET_MAX_LLM_TOKENS` (default 0)
- `CACHE_TTL_SECS` (default 604800 = 7 days)
- `ALLOWLIST_DOMAINS` (comma-separated; optional)
- `PER_DOMAIN_FETCH_CAP` (default 25)
- `MODE` = fast|deep|strict (overrides budgets)

## Operational Rules
- Keep prompts/context minimal.
- Prefer **regex/entity rules** first; only call LLM if `what_to_confirm_next` requires it.
- Log budget counters at the end of each node; include in TXT summary.
