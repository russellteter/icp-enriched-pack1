# Runtime Config

| Var | Meaning | Default |
|-----|---------|---------|
| BUDGET_MAX_SEARCHES | Max search ops per run | 120 |
| BUDGET_MAX_FETCHES | Max URL fetches per run | 150 |
| BUDGET_MAX_ENRICH | Max enrichment calls per run | 80 |
| BUDGET_MAX_LLM_TOKENS | Token ceiling for any LLM usage (0=disabled) | 0 |
| CACHE_TTL_SECS | Cache TTL for fetched pages (seconds) | 604800 |
| ALLOWLIST_DOMAINS | Comma-separated domain allow-list | (empty allows all) |
| PER_DOMAIN_FETCH_CAP | Ceiling per-domain fetches per run | 25 |
| MODE | fast|deep|strict | fast |
