"""
Deduplication Module

Handles deterministic deduplication of organizations and entities
before enrichment and scoring.
"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class DeduplicationResult:
    """Result of deduplication process."""
    unique_organizations: List[Dict]
    duplicates_removed: int
    confidence_scores: Dict[str, float]


class Deduplicator:
    """Handles deduplication of healthcare organizations."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        
        # Common organization name variations
        self.name_variations = {
            'university': ['univ', 'university'],
            'medical': ['med', 'medical'],
            'center': ['centre', 'center', 'ctr'],
            'health': ['health', 'healthcare'],
            'system': ['system', 'systems'],
            'hospital': ['hosp', 'hospital'],
            'clinic': ['clinic', 'cln'],
            'associates': ['assoc', 'associates'],
            'group': ['grp', 'group'],
            'partners': ['partners', 'ptnrs'],
        }
    
    def normalize_organization_name(self, name: str) -> str:
        """
        Normalize organization name for comparison.
        
        Args:
            name: Raw organization name
            
        Returns:
            Normalized name string
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common legal suffixes
        legal_suffixes = [
            r'\b(inc|llc|ltd|corporation|corp|company|co|limited|incorporated)\b',
            r'\b(health|healthcare|medical|center|clinic|hospital|system|group|associates|partners)\b'
        ]
        
        for suffix_pattern in legal_suffixes:
            normalized = re.sub(suffix_pattern, '', normalized, flags=re.IGNORECASE)
        
        # Remove punctuation and extra whitespace
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two organization names.
        
        Args:
            name1: First organization name
            name2: Second organization name
            
        Returns:
            Similarity score between 0 and 1
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize both names
        norm1 = self.normalize_organization_name(name1)
        norm2 = self.normalize_organization_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Boost similarity for exact word matches
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if words1 and words2:
            word_overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))
            # Combine sequence similarity with word overlap
            similarity = (similarity + word_overlap) / 2
        
        return similarity
    
    def find_duplicates(self, organizations: List[Dict]) -> List[Tuple[int, int, float]]:
        """
        Find duplicate organizations in the list.
        
        Args:
            organizations: List of organization dictionaries
            
        Returns:
            List of tuples (index1, index2, similarity_score)
        """
        duplicates = []
        
        for i in range(len(organizations)):
            for j in range(i + 1, len(organizations)):
                org1 = organizations[i]
                org2 = organizations[j]
                
                name1 = org1.get('organization', '')
                name2 = org2.get('organization', '')
                
                similarity = self.calculate_similarity(name1, name2)
                
                if similarity >= self.similarity_threshold:
                    duplicates.append((i, j, similarity))
        
        return duplicates
    
    def deduplicate_organizations(self, organizations: List[Dict]) -> DeduplicationResult:
        """
        Remove duplicate organizations from the list.
        
        Args:
            organizations: List of organization dictionaries
            
        Returns:
            DeduplicationResult with unique organizations and metadata
        """
        if not organizations:
            return DeduplicationResult([], 0, {})
        
        # Find all duplicates
        duplicates = self.find_duplicates(organizations)
        
        # Track which organizations to keep
        to_keep = set(range(len(organizations)))
        confidence_scores = {}
        
        # Process duplicates, keeping the one with more complete data
        for idx1, idx2, similarity in duplicates:
            if idx1 not in to_keep or idx2 not in to_keep:
                continue
            
            org1 = organizations[idx1]
            org2 = organizations[idx2]
            
            # Calculate data completeness scores
            score1 = self._calculate_completeness_score(org1)
            score2 = self._calculate_completeness_score(org2)
            
            # Keep the organization with higher completeness score
            if score1 >= score2:
                to_remove = idx2
                confidence_scores[org1.get('organization', '')] = similarity
            else:
                to_remove = idx1
                confidence_scores[org2.get('organization', '')] = similarity
            
            to_keep.discard(to_remove)
        
        # Create result with unique organizations
        unique_organizations = [organizations[i] for i in sorted(to_keep)]
        duplicates_removed = len(organizations) - len(unique_organizations)
        
        return DeduplicationResult(
            unique_organizations=unique_organizations,
            duplicates_removed=duplicates_removed,
            confidence_scores=confidence_scores
        )
    
    def _calculate_completeness_score(self, org: Dict) -> float:
        """
        Calculate completeness score for an organization.
        
        Args:
            org: Organization dictionary
            
        Returns:
            Completeness score between 0 and 1
        """
        required_fields = ['organization', 'region', 'evidence_url']
        optional_fields = ['tier', 'score', 'notes']
        
        score = 0.0
        total_fields = len(required_fields) + len(optional_fields)
        
        # Check required fields (weighted higher)
        for field in required_fields:
            value = org.get(field, '').strip()
            if value and value.lower() not in ['', 'na', 'n/a', 'none']:
                score += 2.0  # Higher weight for required fields
        
        # Check optional fields
        for field in optional_fields:
            value = org.get(field, '').strip()
            if value and value.lower() not in ['', 'na', 'n/a', 'none']:
                score += 1.0
        
        return score / (len(required_fields) * 2 + len(optional_fields))


# Global instance for easy access
deduplicator = Deduplicator()
