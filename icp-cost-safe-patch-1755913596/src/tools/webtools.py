from duckduckgo_search import DDGS
import httpx, trafilatura, urllib.parse
from tenacity import retry, stop_after_attempt, wait_exponential
from src.runtime.budget import BudgetExceeded
from src.runtime.cache import DiskCache

class WebSearch:
    def __init__(self, budget, cfg):
        self.budget = budget
        self.cfg = cfg

    def search(self, q: str, max_results: int = 10, site: str | None = None):
        self.budget.assert_can_search()
        query = f"{q} site:{site}" if site else q
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        self.budget.tick_search()
        return results

class WebFetch:
    def __init__(self, budget, cfg, cache_dir=".cache/web"):
        self.budget = budget
        self.cfg = cfg
        self.cache = DiskCache(cache_dir, cfg.cache_ttl)

    def _domain(self, url:str)->str:
        try:
            return urllib.parse.urlparse(url).netloc.lower()
        except Exception:
            return ""

    def _allowed(self, domain:str)->bool:
        return (not self.cfg.allowlist) or (domain in self.cfg.allowlist)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def fetch(self, url: str) -> dict:
        cached = self.cache.get(url)
        if cached:
            return cached
        domain = self._domain(url)
        if not self._allowed(domain):
            raise BudgetExceeded(f"Domain not in allow-list: {domain}")
        self.budget.assert_can_fetch(domain)
        with httpx.Client(timeout=20.0, follow_redirects=True) as s:
            r = s.get(url, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            text = trafilatura.extract(r.text, include_links=True, include_formatting=False)
            data = {"status": r.status_code, "url": str(r.url), "html": r.text, "text": text or ""}
            self.cache.set(url, data)
            self.budget.tick_fetch(domain)
            return data
