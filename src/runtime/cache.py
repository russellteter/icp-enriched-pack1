import time, hashlib, json
from pathlib import Path


class DiskCache:
    def __init__(self, base_dir: str, ttl_secs: int = 7 * 24 * 3600):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_secs

    def _key(self, url: str) -> Path:
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.base / f"{h}.json"

    def get(self, url: str):
        p = self._key(url)
        if not p.exists():
            return None
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if time.time() - obj.get("ts", 0) > self.ttl:
                return None
            return obj.get("data")
        except Exception:
            return None

    def set(self, url: str, data: dict):
        p = self._key(url)
        obj = {"ts": time.time(), "data": data}
        p.write_text(json.dumps(obj), encoding="utf-8")


