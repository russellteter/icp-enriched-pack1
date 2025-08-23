import argparse, csv, sys
from pathlib import Path


def load_headers(schema_path: Path):
    line = schema_path.read_text(encoding="utf-8").strip()
    return [h.strip() for h in line.split(",") if h.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--csv", required=True)
    args = ap.parse_args()

    schema_headers = load_headers(Path(args.schema))
    with open(args.csv, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        csv_headers = next(r, [])
        if csv_headers != schema_headers:
            print("Header mismatch")
            print("Expected:", schema_headers)
            print("Got     :", csv_headers)
            sys.exit(1)
        org_idx = csv_headers.index("Organization")
        tier_idx = csv_headers.index("Tier")
        ok = True
        for i, row in enumerate(r, start=2):
            if not (row[org_idx] and row[tier_idx]):
                print(f"Row {i} missing required fields (Organization/Tier)")
                ok = False
        sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
