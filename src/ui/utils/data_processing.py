"""
Data processing utilities for ICP Discovery Engine UI.
Provides data transformation, validation, and formatting functions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime
import json


def normalize_csv_data(csv_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Normalize CSV data from API response into a consistent DataFrame format.
    
    Args:
        csv_data: List of dictionaries from API response
        
    Returns:
        pd.DataFrame: Normalized data with consistent column names
    """
    if not csv_data:
        return pd.DataFrame()
    
    # Standard column mapping
    column_mapping = {
        'organization': 'Organization',
        'tier': 'Tier', 
        'score': 'Score',
        'region': 'Region',
        'evidence_url': 'Evidence_URL',
        'notes': 'Notes',
        'type': 'Type',
        'facilities': 'Facilities',
        'ehr_vendor': 'EHR_Vendor',
        'confidence': 'Confidence',
        'ehr_lifecycle_phase': 'EHR_Lifecycle_Phase',
        'golive_date': 'GoLive_Date',
        'training_model': 'Training_Model',
        'vilt_evidence': 'VILT_Evidence',
        'web_conferencing': 'Web_Conferencing',
        'lms': 'LMS'
    }
    
    # Normalize data
    normalized_data = []
    for item in csv_data:
        normalized_item = {}
        
        # Apply column mapping
        for api_key, display_key in column_mapping.items():
            value = item.get(api_key, item.get(display_key, ''))
            normalized_item[display_key] = value
            
        # Ensure required columns exist
        if 'Organization' not in normalized_item or not normalized_item['Organization']:
            normalized_item['Organization'] = 'Unknown Organization'
            
        normalized_data.append(normalized_item)
    
    return pd.DataFrame(normalized_data)


def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate data quality and completeness.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dict containing validation results
    """
    if df.empty:
        return {
            'is_valid': False,
            'errors': ['DataFrame is empty'],
            'warnings': [],
            'completeness_score': 0.0
        }
    
    errors = []
    warnings = []
    
    # Required columns check
    required_columns = ['Organization', 'Tier', 'Region']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
    
    # Data completeness check
    if 'Organization' in df.columns:
        empty_orgs = df['Organization'].isna() | (df['Organization'] == '')
        if empty_orgs.any():
            warnings.append(f"{empty_orgs.sum()} rows have empty organization names")
    
    # Score validation
    if 'Score' in df.columns:
        invalid_scores = df['Score'].apply(lambda x: not isinstance(x, (int, float)) or pd.isna(x) or x < 0 or x > 100)
        if invalid_scores.any():
            warnings.append(f"{invalid_scores.sum()} rows have invalid scores (should be 0-100)")
    
    # Tier validation
    if 'Tier' in df.columns:
        valid_tiers = ['Confirmed', 'Probable', 'Excluded', 'Tier 1', 'Tier 2', 'Tier 3']
        invalid_tiers = ~df['Tier'].isin(valid_tiers) & df['Tier'].notna()
        if invalid_tiers.any():
            unique_invalid = df.loc[invalid_tiers, 'Tier'].unique()
            warnings.append(f"Unexpected tier values: {list(unique_invalid)}")
    
    # Calculate completeness score
    total_cells = len(df) * len(df.columns)
    filled_cells = df.notna().sum().sum()
    completeness_score = filled_cells / total_cells if total_cells > 0 else 0.0
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'completeness_score': completeness_score,
        'total_rows': len(df),
        'total_columns': len(df.columns)
    }


def calculate_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate quality metrics from the data.
    
    Args:
        df: DataFrame containing results data
        
    Returns:
        Dict containing quality metrics
    """
    if df.empty:
        return {}
    
    metrics = {
        'total_results': len(df)
    }
    
    # Tier distribution
    if 'Tier' in df.columns:
        tier_counts = df['Tier'].value_counts().to_dict()
        metrics['tier_distribution'] = tier_counts
        
        # Quality rate (Confirmed + Tier 1)
        high_quality = df['Tier'].str.contains('Confirmed|Tier 1', case=False, na=False).sum()
        metrics['quality_rate'] = high_quality / len(df) if len(df) > 0 else 0
        metrics['high_quality_count'] = high_quality
    
    # Score statistics
    if 'Score' in df.columns and df['Score'].notna().any():
        score_data = df['Score'].dropna()
        metrics['score_stats'] = {
            'mean': float(score_data.mean()),
            'median': float(score_data.median()),
            'min': float(score_data.min()),
            'max': float(score_data.max()),
            'std': float(score_data.std())
        }
    
    # Regional distribution
    if 'Region' in df.columns:
        region_counts = df['Region'].value_counts().to_dict()
        metrics['regional_distribution'] = region_counts
    
    # Evidence coverage
    if 'Evidence_URL' in df.columns:
        has_evidence = (df['Evidence_URL'].notna() & (df['Evidence_URL'] != '')).sum()
        metrics['evidence_coverage'] = has_evidence / len(df) if len(df) > 0 else 0
    
    return metrics


def extract_domains_from_urls(df: pd.DataFrame, url_column: str = 'Evidence_URL') -> pd.Series:
    """
    Extract domains from URLs in the specified column.
    
    Args:
        df: DataFrame containing URLs
        url_column: Name of column containing URLs
        
    Returns:
        pd.Series: Series of domains
    """
    if url_column not in df.columns:
        return pd.Series(dtype=str)
    
    urls = df[url_column].dropna()
    if urls.empty:
        return pd.Series(dtype=str)
    
    # Extract domain from URL using regex
    domain_pattern = r'https?://(?:www\.)?([^/]+)'
    domains = urls.str.extract(domain_pattern, expand=False)
    
    return domains.dropna()


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency for display."""
    if currency == 'USD':
        return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage for display."""
    return f"{value:.{decimals}%}"


def format_large_number(number: int) -> str:
    """Format large numbers with appropriate suffixes."""
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)


def clean_organization_names(df: pd.DataFrame, org_column: str = 'Organization') -> pd.DataFrame:
    """
    Clean and standardize organization names.
    
    Args:
        df: DataFrame to clean
        org_column: Name of organization column
        
    Returns:
        pd.DataFrame: DataFrame with cleaned organization names
    """
    if org_column not in df.columns:
        return df
    
    df = df.copy()
    
    # Remove common suffixes/prefixes
    suffixes = [' Inc.', ' Inc', ' LLC', ' Corp.', ' Corp', ' Ltd.', ' Ltd', ' LP', ' LLP']
    prefixes = ['The ']
    
    for suffix in suffixes:
        df[org_column] = df[org_column].str.replace(suffix, '', case=False)
    
    for prefix in prefixes:
        df[org_column] = df[org_column].str.replace(f'^{prefix}', '', case=False, regex=True)
    
    # Trim whitespace
    df[org_column] = df[org_column].str.strip()
    
    return df


def detect_duplicates(df: pd.DataFrame, org_column: str = 'Organization', similarity_threshold: float = 0.8) -> pd.DataFrame:
    """
    Detect potential duplicate organizations.
    
    Args:
        df: DataFrame to check
        org_column: Name of organization column
        similarity_threshold: Threshold for similarity detection
        
    Returns:
        pd.DataFrame: DataFrame with duplicate flags
    """
    if org_column not in df.columns or df.empty:
        return df
    
    df = df.copy()
    df['is_potential_duplicate'] = False
    
    # Simple duplicate detection based on name similarity
    org_names = df[org_column].str.lower().str.strip()
    
    for i, name in enumerate(org_names):
        if pd.isna(name):
            continue
            
        # Find similar names
        similar_mask = org_names.str.contains(name[:10], case=False, na=False) if len(name) > 10 else False
        
        if similar_mask.any() and similar_mask.sum() > 1:
            df.loc[similar_mask, 'is_potential_duplicate'] = True
    
    return df


def prepare_export_data(df: pd.DataFrame, export_format: str = 'csv') -> pd.DataFrame:
    """
    Prepare data for export in specified format.
    
    Args:
        df: DataFrame to prepare
        export_format: Target export format ('csv', 'excel')
        
    Returns:
        pd.DataFrame: Prepared DataFrame
    """
    if df.empty:
        return df
    
    df_export = df.copy()
    
    # Standardize column order
    priority_columns = [
        'Organization', 'Tier', 'Score', 'Region', 'Type', 
        'EHR_Vendor', 'Evidence_URL', 'Confidence', 'Notes'
    ]
    
    # Reorder columns
    available_priority = [col for col in priority_columns if col in df_export.columns]
    remaining_columns = [col for col in df_export.columns if col not in priority_columns]
    column_order = available_priority + remaining_columns
    
    df_export = df_export[column_order]
    
    # Format for specific export types
    if export_format == 'excel':
        # Limit text fields for Excel compatibility
        text_columns = df_export.select_dtypes(include=['object']).columns
        for col in text_columns:
            df_export[col] = df_export[col].astype(str).str[:32767]  # Excel cell limit
    
    return df_export


def generate_summary_stats(df: pd.DataFrame) -> str:
    """
    Generate a text summary of the data.
    
    Args:
        df: DataFrame to summarize
        
    Returns:
        str: Text summary
    """
    if df.empty:
        return "No data available for summary."
    
    summary_parts = []
    
    # Basic stats
    summary_parts.append(f"Total Results: {len(df)}")
    
    # Quality breakdown
    if 'Tier' in df.columns:
        tier_counts = df['Tier'].value_counts()
        summary_parts.append("\nQuality Breakdown:")
        for tier, count in tier_counts.items():
            percentage = (count / len(df)) * 100
            summary_parts.append(f"  {tier}: {count} ({percentage:.1f}%)")
    
    # Regional distribution
    if 'Region' in df.columns:
        region_counts = df['Region'].value_counts()
        summary_parts.append("\nRegional Distribution:")
        for region, count in region_counts.items():
            percentage = (count / len(df)) * 100
            summary_parts.append(f"  {region}: {count} ({percentage:.1f}%)")
    
    # Score statistics
    if 'Score' in df.columns and df['Score'].notna().any():
        scores = df['Score'].dropna()
        summary_parts.append(f"\nScore Statistics:")
        summary_parts.append(f"  Average: {scores.mean():.1f}")
        summary_parts.append(f"  Range: {scores.min():.0f} - {scores.max():.0f}")
    
    return "\n".join(summary_parts)