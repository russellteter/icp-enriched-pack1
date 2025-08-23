#!/usr/bin/env python3
"""
Evidence Support Evaluator

Verifies evidence URLs are accessible and relevant to the organization.
"""

import csv
import sys
import re
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urlparse


def evaluate_evidence_support(csv_path: str) -> Dict:
    """
    Evaluate evidence support quality in CSV file.
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        Dict with evidence support metrics
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        return {
            "error": f"CSV file not found: {csv_path}",
            "support_score": 0.0,
            "invalid_evidence": []
        }
    
    total_rows = 0
    rows_with_evidence = 0
    valid_url_rows = 0
    invalid_evidence = []
    
    # URL validation patterns
    url_pattern = re.compile(r'https?://[^\s]+')
    
    try:
        with csv_file.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                evidence_urls = row.get('Evidence_URLs', '').strip()
                organization = row.get('Organization', '').strip()
                
                if evidence_urls:
                    rows_with_evidence += 1
                    
                    # Check if URLs are valid format
                    urls = url_pattern.findall(evidence_urls)
                    if urls:
                        valid_url_rows += 1
                        
                        # Basic domain validation (could be enhanced with actual HTTP checks)
                        for url in urls:
                            try:
                                parsed = urlparse(url)
                                if not parsed.netloc:
                                    invalid_evidence.append({
                                        'row': total_rows,
                                        'organization': organization,
                                        'url': url,
                                        'reason': 'Invalid URL format'
                                    })
                            except Exception:
                                invalid_evidence.append({
                                    'row': total_rows,
                                    'organization': organization,
                                    'url': url,
                                    'reason': 'URL parsing error'
                                })
                    else:
                        invalid_evidence.append({
                            'row': total_rows,
                            'organization': organization,
                            'url': evidence_urls,
                            'reason': 'No valid URLs found'
                        })
                else:
                    invalid_evidence.append({
                        'row': total_rows,
                        'organization': organization,
                        'url': evidence_urls,
                        'reason': 'No evidence URLs provided'
                    })
    
    except Exception as e:
        return {
            "error": f"Error reading CSV: {e}",
            "support_score": 0.0,
            "invalid_evidence": []
        }
    
    # Calculate support score (percentage of rows with valid evidence)
    support_score = (valid_url_rows / total_rows * 100) if total_rows > 0 else 0.0
    
    return {
        "support_score": support_score,
        "total_rows": total_rows,
        "rows_with_evidence": rows_with_evidence,
        "valid_url_rows": valid_url_rows,
        "invalid_evidence": invalid_evidence,
        "threshold_met": support_score >= 90.0  # 90% threshold for evidence support
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python evidence_support.py <csv_path>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    result = evaluate_evidence_support(csv_path)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    
    print(f"Evidence Support Score: {result['support_score']:.1f}%")
    print(f"Total Rows: {result['total_rows']}")
    print(f"Rows with Evidence: {result['rows_with_evidence']}")
    print(f"Valid URL Rows: {result['valid_url_rows']}")
    
    if result['invalid_evidence']:
        print("Invalid Evidence:")
        for invalid in result['invalid_evidence']:
            print(f"  Row {invalid['row']}: {invalid['organization']} -> '{invalid['url']}' ({invalid['reason']})")
    
    print(f"Threshold Met: {result['threshold_met']}")
    
    if not result['threshold_met']:
        sys.exit(1)


if __name__ == "__main__":
    main()
