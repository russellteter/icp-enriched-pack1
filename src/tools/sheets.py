class SheetsLedger:
    def load_orgs(self, segment: str) -> set[str]:
        return set()

    def upsert(self, rows: list[dict]):
        return {"upserted": len(rows)}


