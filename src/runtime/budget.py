class BudgetExceeded(Exception):
    pass


class BudgetManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.searches = 0
        self.fetches = 0
        self.enrich = 0
        self.llm_tokens = 0
        self.per_domain = {}

    def assert_can_search(self):
        if self.searches >= self.cfg.max_searches:
            raise BudgetExceeded("Search budget exceeded")

    def tick_search(self, n=1):
        self.searches += n

    def assert_can_fetch(self, domain: str):
        if self.fetches >= self.cfg.max_fetches:
            raise BudgetExceeded("Fetch budget exceeded")
        if self.cfg.per_domain_cap and domain:
            used = self.per_domain.get(domain, 0)
            if used >= self.cfg.per_domain_cap:
                raise BudgetExceeded(f"Per-domain cap exceeded for {domain}")

    def tick_fetch(self, domain: str):
        self.fetches += 1
        if domain:
            self.per_domain[domain] = self.per_domain.get(domain, 0) + 1

    def assert_can_enrich(self):
        if self.enrich >= self.cfg.max_enrich:
            raise BudgetExceeded("Enrich budget exceeded")

    def tick_enrich(self):
        self.enrich += 1

    def assert_can_use_tokens(self, n):
        if (self.llm_tokens + n) > self.cfg.max_llm_tokens:
            raise BudgetExceeded("LLM token budget exceeded")

    def tick_tokens(self, n):
        self.llm_tokens += n

    def snapshot(self):
        return {
            "mode": self.cfg.mode,
            "searches": self.searches,
            "fetches": self.fetches,
            "enrich": self.enrich,
            "llm_tokens": self.llm_tokens,
            "per_domain": self.per_domain,
        }


