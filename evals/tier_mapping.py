#!/usr/bin/env python3
"""
Tier Mapping Evaluator

Validates tier assignments against business rules and scoring logic.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List, Set


def evaluate_tier_mapping(csv_path: str) -> Dict:
    """
    Evaluate tier mapping validity in CSV file.
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        Dict with tier mapping metrics
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        return {
            "error": f"CSV file not found: {csv_path}",
            "validity": 0.0,
            "invalid_tiers": []
        }
    
    # Valid tier values based on business rules
    valid_tiers = {"Tier 1", "Tier 2", "Tier 3"}
    
    total_rows = 0
    valid_tier_rows = 0
    invalid_tiers = []
    tier_distribution = {tier: 0 for tier in valid_tiers}
    
    try:
        with csv_file.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                tier = row.get('Tier', '').strip()
                
                if tier in valid_tiers:
                    valid_tier_rows += 1
                    tier_distribution[tier] += 1
                else:
                    invalid_tiers.append({
                        'row': total_rows,
                        'organization': row.get('Organization', 'Unknown'),
                        'tier': tier,
                        'confidence': row.get('Confidence', 'N/A')
                    })
    
    except Exception as e:
        return {
            "error": f"Error reading CSV: {e}",
            "validity": 0.0,
            "invalid_tiers": []
        }
    
    validity = (valid_tier_rows / total_rows * 100) if total_rows > 0 else 0.0
    
    return {
        "validity": validity,
        "total_rows": total_rows,
        "valid_tier_rows": valid_tier_rows,
        "tier_distribution": {k: v for k, v in tier_distribution.items() if v > 0},
        "invalid_tiers": invalid_tiers,
        "threshold_met": validity >= 100.0
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python tier_mapping.py <csv_path>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    result = evaluate_tier_mapping(csv_path)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    
    print(f"Tier Mapping Validity: {result['validity']:.1f}%")
    print(f"Total Rows: {result['total_rows']}")
    print(f"Valid Tier Rows: {result['valid_tier_rows']}")
    
    if result['tier_distribution']:
        print("Tier Distribution:")
        for tier, count in result['tier_distribution'].items():
            print(f"  {tier}: {count} rows")
    
    if result['invalid_tiers']:
        print("Invalid Tiers:")
        for invalid in result['invalid_tiers']:
            print(f"  Row {invalid['row']}: {invalid['organization']} -> '{invalid['tier']}' (confidence: {invalid['confidence']})")
    
    print(f"Threshold Met: {result['threshold_met']}")
    
    if not result['threshold_met']:
        sys.exit(1)


if __name__ == "__main__":
    main()
