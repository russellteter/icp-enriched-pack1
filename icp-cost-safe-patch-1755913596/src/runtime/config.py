import os

def env_int(key, default):
    try:
        return int(os.getenv(key, default))
    except Exception:
        return default

def env_set(key):
    v = os.getenv(key, "").strip()
    return set([x.strip().lower() for x in v.split(",") if x.strip()]) if v else set()

class RunConfig:
    def __init__(self, mode: str = None):
        self.mode = (mode or os.getenv("MODE","fast")).lower()
        self.max_searches = env_int("BUDGET_MAX_SEARCHES", 120)
        self.max_fetches = env_int("BUDGET_MAX_FETCHES", 150)
        self.max_enrich = env_int("BUDGET_MAX_ENRICH", 80)
        self.max_llm_tokens = env_int("BUDGET_MAX_LLM_TOKENS", 0)
        self.cache_ttl = env_int("CACHE_TTL_SECS", 7*24*3600)
        self.allowlist = env_set("ALLOWLIST_DOMAINS")
        self.per_domain_cap = env_int("PER_DOMAIN_FETCH_CAP", 25)
        if self.mode == "deep":
            self.max_searches *= 2
            self.max_fetches *= 2
            self.max_enrich = int(self.max_enrich * 1.5)
        if self.mode == "strict":
            self.max_searches //= 2
            self.max_fetches //= 2
            self.max_enrich //= 2
