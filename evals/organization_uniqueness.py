#!/usr/bin/env python3
"""
Organization Uniqueness Evaluator
Detects potential duplicate organizations in the results
"""

import sys
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Set
import re
from difflib import SequenceMatcher


def normalize_organization_name(name: str) -> str:
    """Normalize organization name for comparison"""
    if not name:
        return ''
    
    # Convert to lowercase
    normalized = name.lower().strip()
    
    # Remove common suffixes and prefixes
    suffixes_to_remove = [
        r'\s+inc\.?$', r'\s+llc\.?$', r'\s+corp\.?$', r'\s+ltd\.?$', 
        r'\s+company$', r'\s+co\.?$', r'\s+corporation$', r'\s+limited$',
        r'\s+group$', r'\s+systems?$', r'\s+solutions?$', r'\s+services?$',
        r'\s+international$', r'\s+global$', r'\s+worldwide$',
        r'\s+healthcare$', r'\s+health$', r'\s+medical$', r'\s+hospital$',
        r'\s+training$', r'\s+academy$', r'\s+university$', r'\s+institute$'
    ]
    
    for suffix in suffixes_to_remove:
        normalized = re.sub(suffix, '', normalized)
    
    # Remove extra whitespace and special characters
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def calculate_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two organization names"""
    norm1 = normalize_organization_name(name1)
    norm2 = normalize_organization_name(name2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Sequence matching
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Boost similarity if one name contains the other
    if norm1 in norm2 or norm2 in norm1:
        similarity = max(similarity, 0.8)
    
    # Check for common word overlap
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if words1 and words2:
        word_overlap = len(words1.intersection(words2)) / min(len(words1), len(words2))
        if word_overlap >= 0.8:  # 80% of words overlap
            similarity = max(similarity, 0.9)
    
    return similarity


def find_potential_duplicates(organizations: List[str], threshold: float = 0.85) -> List[Tuple[str, str, float]]:
    """Find potential duplicate organizations"""
    duplicates = []
    
    for i in range(len(organizations)):
        for j in range(i + 1, len(organizations)):
            similarity = calculate_similarity(organizations[i], organizations[j])
            if similarity >= threshold:
                duplicates.append((organizations[i], organizations[j], similarity))
    
    return duplicates


def evaluate_organization_uniqueness(csv_path: Path) -> Tuple[float, Dict]:
    """Evaluate organization uniqueness in the CSV"""
    
    if not csv_path.exists():
        return 0.0, {'error': f'CSV file not found: {csv_path}'}
    
    organizations = []
    total_rows = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                
                # Get organization name
                org_name = (row.get('Organization') or row.get('Company') or '').strip()
                if org_name:
                    organizations.append(org_name)
    
    except Exception as e:
        return 0.0, {'error': f'Error reading CSV: {str(e)}'}
    
    if not organizations:
        return 0.0, {'error': 'No organization names found in CSV'}
    
    # Find potential duplicates
    duplicates = find_potential_duplicates(organizations)
    
    # Calculate uniqueness score
    unique_orgs = len(set(normalize_organization_name(org) for org in organizations))
    uniqueness_ratio = unique_orgs / len(organizations) if organizations else 0
    
    # Penalize for high-confidence duplicates
    high_confidence_dupes = [d for d in duplicates if d[2] >= 0.95]
    medium_confidence_dupes = [d for d in duplicates if 0.85 <= d[2] < 0.95]
    
    # Calculate final score
    penalty = (len(high_confidence_dupes) * 2 + len(medium_confidence_dupes)) / len(organizations)
    final_score = max(0, uniqueness_ratio - penalty)
    
    return final_score, {
        'total_organizations': len(organizations),
        'unique_normalized': unique_orgs,
        'uniqueness_ratio': uniqueness_ratio * 100,
        'potential_duplicates': len(duplicates),
        'high_confidence_duplicates': len(high_confidence_dupes),
        'medium_confidence_duplicates': len(medium_confidence_dupes),
        'final_score': final_score * 100,
        'sample_duplicates': duplicates[:5],  # Show first 5 duplicates
        'duplicate_details': [
            {
                'org1': d[0],
                'org2': d[1], 
                'similarity': f"{d[2]:.2f}",
                'normalized1': normalize_organization_name(d[0]),
                'normalized2': normalize_organization_name(d[1])
            }
            for d in duplicates[:3]
        ]
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m evals.organization_uniqueness <csv_file>")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    
    score, details = evaluate_organization_uniqueness(csv_path)
    
    print(f"Organization Uniqueness Evaluation for {csv_path.name}")
    print("=" * 60)
    
    if 'error' in details:
        print(f"❌ Error: {details['error']}")
        sys.exit(1)
    
    print(f"Total organizations: {details['total_organizations']}")
    print(f"Unique (normalized): {details['unique_normalized']}")
    print(f"Uniqueness ratio: {details['uniqueness_ratio']:.1f}%")
    print(f"Potential duplicates: {details['potential_duplicates']}")
    print(f"High confidence duplicates (≥95%): {details['high_confidence_duplicates']}")
    print(f"Medium confidence duplicates (85-95%): {details['medium_confidence_duplicates']}")
    print(f"Final uniqueness score: {details['final_score']:.1f}%")
    
    # Threshold: 90% uniqueness
    threshold = 90.0
    
    if details['final_score'] >= threshold:
        print(f"✅ PASS: Organization uniqueness meets {threshold}% threshold")
    else:
        print(f"❌ FAIL: Organization uniqueness below {threshold}% threshold")
        
        if details['potential_duplicates'] > 0:
            print(f"\nSample potential duplicates:")
            for dup in details['duplicate_details']:
                print(f"  • '{dup['org1']}' ≈ '{dup['org2']}' (similarity: {dup['similarity']})")
                print(f"    normalized: '{dup['normalized1']}' vs '{dup['normalized2']}'")
    
    print()


if __name__ == "__main__":
    main()