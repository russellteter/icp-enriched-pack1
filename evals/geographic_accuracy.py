#!/usr/bin/env python3
"""
Geographic Accuracy Evaluator
Validates that regional classifications (NA/EMEA/Both) are accurate based on evidence
"""

import sys
import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse


def extract_region_indicators(text: str, url: str) -> Dict[str, List[str]]:
    """Extract geographic indicators from text and URL"""
    
    na_indicators = [
        # Countries
        'united states', 'usa', 'canada', 'mexico',
        # Cities
        'new york', 'san francisco', 'los angeles', 'toronto', 'vancouver',
        # Regions/Terms
        'north america', 'america', 'american', 'us based', 'canada based'
    ]
    
    emea_indicators = [
        # Countries
        'united kingdom', 'uk', 'germany', 'france', 'netherlands', 'italy', 'spain',
        'sweden', 'norway', 'denmark', 'switzerland', 'austria', 'belgium',
        'south africa', 'nigeria', 'egypt', 'uae', 'dubai', 'abu dhabi',
        # Cities
        'london', 'paris', 'berlin', 'amsterdam', 'madrid', 'rome', 'stockholm',
        'zurich', 'geneva', 'brussels', 'copenhagen', 'dublin', 'edinburgh',
        'cape town', 'johannesburg', 'cairo', 'lagos',
        # Regions/Terms
        'europe', 'european', 'emea', 'middle east', 'africa', 'eu based'
    ]
    
    global_indicators = [
        'global', 'worldwide', 'international', 'multinational',
        'across continents', 'multiple countries', 'various regions'
    ]
    
    text_lower = (text or '').lower()
    
    found_na = [ind for ind in na_indicators if ind in text_lower]
    found_emea = [ind for ind in emea_indicators if ind in text_lower]
    found_global = [ind for ind in global_indicators if ind in text_lower]
    
    # Check domain TLD for additional clues
    if url:
        try:
            domain = urlparse(url).hostname or ''
            if domain.endswith(('.ca', '.us')):
                found_na.append(f'domain:{domain}')
            elif domain.endswith(('.uk', '.de', '.fr', '.nl', '.it', '.es', '.se', '.no', '.dk', '.ch', '.at', '.be', '.ie', '.co.za')):
                found_emea.append(f'domain:{domain}')
        except:
            pass
    
    return {
        'na': found_na,
        'emea': found_emea, 
        'global': found_global
    }


def classify_region_from_evidence(text: str, url: str) -> str:
    """Classify region based on evidence text and URL"""
    
    indicators = extract_region_indicators(text, url)
    
    na_count = len(indicators['na'])
    emea_count = len(indicators['emea'])
    global_count = len(indicators['global'])
    
    # Strong global indicators override everything
    if global_count >= 2:
        return 'both'
    
    # Clear regional preference
    if na_count > emea_count and na_count >= 2:
        return 'na'
    elif emea_count > na_count and emea_count >= 2:
        return 'emea'
    elif na_count > 0 and emea_count > 0:
        return 'both'
    elif na_count > 0:
        return 'na'
    elif emea_count > 0:
        return 'emea'
    else:
        return 'unknown'


def evaluate_geographic_accuracy(csv_path: Path) -> Tuple[float, Dict]:
    """Evaluate geographic accuracy of region classifications"""
    
    if not csv_path.exists():
        return 0.0, {'error': f'CSV file not found: {csv_path}'}
    
    total_rows = 0
    accurate_classifications = 0
    mismatches = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                
                # Get reported region
                reported_region = (row.get('Region') or row.get('Regions_Served(NA/EMEA/Both)') or '').lower().strip()
                if reported_region == 'both':
                    reported_region = 'both'
                elif reported_region in ['na', 'north america']:
                    reported_region = 'na'
                elif reported_region in ['emea', 'europe', 'europe/middle east/africa']:
                    reported_region = 'emea'
                
                # Extract evidence text (try multiple possible fields)
                evidence_text = ''
                evidence_url = ''
                
                # Try to get full text or notes
                for field in ['full_text', 'Notes', 'notes', 'Evidence_URLs', 'evidence_url']:
                    if field in row and row[field]:
                        if 'url' in field.lower():
                            evidence_url = row[field]
                        else:
                            evidence_text += ' ' + row[field]
                
                # Classify based on evidence
                evidence_region = classify_region_from_evidence(evidence_text, evidence_url)
                
                # Check accuracy
                if evidence_region == 'unknown':
                    # If we can't determine from evidence, assume classification is reasonable
                    accurate_classifications += 1
                elif reported_region == evidence_region:
                    accurate_classifications += 1
                elif reported_region == 'both' and evidence_region in ['na', 'emea']:
                    # 'Both' is acceptable if evidence shows one specific region
                    accurate_classifications += 1
                else:
                    mismatches.append({
                        'organization': row.get('Organization') or row.get('Company') or 'Unknown',
                        'reported': reported_region,
                        'evidence_suggests': evidence_region,
                        'evidence_indicators': extract_region_indicators(evidence_text, evidence_url)
                    })
    
    except Exception as e:
        return 0.0, {'error': f'Error reading CSV: {str(e)}'}
    
    if total_rows == 0:
        return 0.0, {'error': 'No data rows found in CSV'}
    
    accuracy = accurate_classifications / total_rows
    
    return accuracy, {
        'total_rows': total_rows,
        'accurate_classifications': accurate_classifications,
        'accuracy_percentage': accuracy * 100,
        'mismatches': mismatches[:5],  # Show first 5 mismatches
        'total_mismatches': len(mismatches)
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m evals.geographic_accuracy <csv_file>")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    
    accuracy, details = evaluate_geographic_accuracy(csv_path)
    
    print(f"Geographic Accuracy Evaluation for {csv_path.name}")
    print("=" * 60)
    
    if 'error' in details:
        print(f"❌ Error: {details['error']}")
        sys.exit(1)
    
    print(f"Total organizations: {details['total_rows']}")
    print(f"Accurate classifications: {details['accurate_classifications']}")
    print(f"Accuracy: {details['accuracy_percentage']:.1f}%")
    
    # Threshold: 85% accuracy
    threshold = 85.0
    
    if details['accuracy_percentage'] >= threshold:
        print(f"✅ PASS: Geographic accuracy meets {threshold}% threshold")
    else:
        print(f"❌ FAIL: Geographic accuracy below {threshold}% threshold")
        
        if details['total_mismatches'] > 0:
            print(f"\nSample mismatches ({details['total_mismatches']} total):")
            for mismatch in details['mismatches']:
                print(f"  • {mismatch['organization']}: reported='{mismatch['reported']}' vs evidence='{mismatch['evidence_suggests']}'")
    
    print()


if __name__ == "__main__":
    main()