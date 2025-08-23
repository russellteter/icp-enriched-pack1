#!/usr/bin/env python3
"""
Schema Completeness Evaluator

Ensures all required fields are populated in the CSV output.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List, Set


def evaluate_schema_completeness(csv_path: str, required_fields: Set[str] = None) -> Dict:
    """
    Evaluate schema completeness of CSV file.
    
    Args:
        csv_path: Path to CSV file
        required_fields: Set of required field names (defaults to all healthcare fields)
    
    Returns:
        Dict with completeness metrics
    """
    if required_fields is None:
        required_fields = {
            "Organization", "Region", "Tier", "Confidence", "Evidence_URLs"
        }
    
    csv_file = Path(csv_path)
    if not csv_file.exists():
        return {
            "error": f"CSV file not found: {csv_path}",
            "completeness": 0.0,
            "missing_fields": list(required_fields)
        }
    
    total_rows = 0
    complete_rows = 0
    missing_fields_count = {field: 0 for field in required_fields}
    
    try:
        with csv_file.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                row_complete = True
                
                for field in required_fields:
                    value = row.get(field, '').strip()
                    if not value or value.lower() in ['', 'na', 'n/a', 'none']:
                        missing_fields_count[field] += 1
                        row_complete = False
                
                if row_complete:
                    complete_rows += 1
    
    except Exception as e:
        return {
            "error": f"Error reading CSV: {e}",
            "completeness": 0.0,
            "missing_fields": list(required_fields)
        }
    
    completeness = (complete_rows / total_rows * 100) if total_rows > 0 else 0.0
    
    return {
        "completeness": completeness,
        "total_rows": total_rows,
        "complete_rows": complete_rows,
        "missing_fields": {k: v for k, v in missing_fields_count.items() if v > 0},
        "threshold_met": completeness >= 100.0
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python schema_completeness.py <csv_path>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    result = evaluate_schema_completeness(csv_path)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    
    print(f"Schema Completeness: {result['completeness']:.1f}%")
    print(f"Total Rows: {result['total_rows']}")
    print(f"Complete Rows: {result['complete_rows']}")
    
    if result['missing_fields']:
        print("Missing Fields:")
        for field, count in result['missing_fields'].items():
            print(f"  {field}: {count} rows")
    
    print(f"Threshold Met: {result['threshold_met']}")
    
    if not result['threshold_met']:
        sys.exit(1)


if __name__ == "__main__":
    main()
