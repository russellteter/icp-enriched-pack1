"""
Entity Extraction Rules for Healthcare ICP

Defines patterns and rules for extracting healthcare-specific entities
from web content and organization data.
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class EntityMatch:
    """Represents a matched entity with confidence and context."""
    entity_type: str
    value: str
    confidence: float
    context: str
    source_field: str


class HealthcareEntityExtractor:
    """Extracts healthcare-specific entities from text content."""
    
    def __init__(self):
        # EHR Vendor patterns
        self.ehr_vendors = {
            'Epic': ['epic', 'epic systems', 'epic ehr'],
            'Cerner': ['cerner', 'cerner corporation', 'cerner ehr'],
            'Meditech': ['meditech', 'medical information technology'],
            'Allscripts': ['allscripts', 'allscripts healthcare'],
            'Athenahealth': ['athenahealth', 'athena health'],
            'NextGen': ['nextgen', 'nextgen healthcare'],
            'eClinicalWorks': ['eclinicalworks', 'eclinical works'],
            'Practice Fusion': ['practice fusion'],
            'Greenway Health': ['greenway health', 'greenway'],
            'Kareo': ['kareo'],
            'DrChrono': ['drchrono', 'dr chrono'],
            'AdvancedMD': ['advancedmd', 'advanced md'],
            'CareCloud': ['carecloud', 'care cloud'],
            'Modernizing Medicine': ['modernizing medicine'],
            'CompuGroup Medical': ['compugroup medical', 'cgm'],
            'CPSI': ['cpsi', 'computer programs and systems'],
            'Medhost': ['medhost', 'med host'],
            'Paragon': ['paragon', 'paragon ehr'],
            'Sunrise': ['sunrise', 'sunrise clinical manager'],
            'Soarian': ['soarian', 'soarian clinicals'],
        }
        
        # EHR Lifecycle Phase patterns
        self.ehr_lifecycle_phases = {
            'Planning': ['planning', 'evaluation', 'selection', 'vendor selection'],
            'Implementation': ['implementation', 'go-live', 'deployment', 'rollout'],
            'Optimization': ['optimization', 'enhancement', 'upgrade', 'improvement'],
            'Maintenance': ['maintenance', 'support', 'ongoing', 'operational'],
            'Replacement': ['replacement', 'migration', 'transition', 'new system'],
        }
        
        # Organization type patterns
        self.organization_types = {
            'Hospital': ['hospital', 'medical center', 'health center', 'clinic'],
            'Health System': ['health system', 'healthcare system', 'medical system'],
            'Physician Practice': ['physician practice', 'medical practice', 'doctor office'],
            'Urgent Care': ['urgent care', 'walk-in clinic', 'immediate care'],
            'Specialty Practice': ['specialty', 'specialist', 'cardiology', 'orthopedics'],
            'Long-term Care': ['nursing home', 'long-term care', 'skilled nursing'],
            'Home Health': ['home health', 'homecare', 'home care'],
            'Behavioral Health': ['behavioral health', 'mental health', 'psychiatry'],
            'Rehabilitation': ['rehabilitation', 'rehab', 'physical therapy'],
        }
        
        # Date patterns for Go-live dates
        self.date_patterns = [
            r'\b(?:go-live|go live|implementation|deployment)\s+(?:date|on|in)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'\b(?:go-live|go live|implementation|deployment)\s+(?:date|on|in)?\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})',
            r'\b(?:go-live|go live|implementation|deployment)\s+(?:date|on|in)?\s*:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        ]
        
        # Compile regex patterns
        self.compiled_date_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.date_patterns]
    
    def extract_ehr_vendor(self, text: str) -> Optional[EntityMatch]:
        """Extract EHR vendor from text."""
        text_lower = text.lower()
        
        for vendor, patterns in self.ehr_vendors.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Calculate confidence based on context
                    confidence = 0.8
                    if f"ehr" in text_lower or "electronic health record" in text_lower:
                        confidence = 0.95
                    if f"vendor" in text_lower or "system" in text_lower:
                        confidence = 0.9
                    
                    return EntityMatch(
                        entity_type="EHR_Vendor",
                        value=vendor,
                        confidence=confidence,
                        context=text[:200] + "..." if len(text) > 200 else text,
                        source_field="content"
                    )
        
        return None
    
    def extract_ehr_lifecycle_phase(self, text: str) -> Optional[EntityMatch]:
        """Extract EHR lifecycle phase from text."""
        text_lower = text.lower()
        
        for phase, patterns in self.ehr_lifecycle_phases.items():
            for pattern in patterns:
                if pattern in text_lower:
                    confidence = 0.7
                    if "ehr" in text_lower or "electronic health record" in text_lower:
                        confidence = 0.9
                    
                    return EntityMatch(
                        entity_type="EHR_Lifecycle_Phase",
                        value=phase,
                        confidence=confidence,
                        context=text[:200] + "..." if len(text) > 200 else text,
                        source_field="content"
                    )
        
        return None
    
    def extract_organization_type(self, text: str) -> Optional[EntityMatch]:
        """Extract organization type from text."""
        text_lower = text.lower()
        
        for org_type, patterns in self.organization_types.items():
            for pattern in patterns:
                if pattern in text_lower:
                    confidence = 0.8
                    if org_type.lower() in text_lower:
                        confidence = 0.95
                    
                    return EntityMatch(
                        entity_type="Organization_Type",
                        value=org_type,
                        confidence=confidence,
                        context=text[:200] + "..." if len(text) > 200 else text,
                        source_field="content"
                    )
        
        return None
    
    def extract_go_live_date(self, text: str) -> Optional[EntityMatch]:
        """Extract go-live date from text."""
        for pattern in self.compiled_date_patterns:
            match = pattern.search(text)
            if match:
                date_str = match.group(1)
                return EntityMatch(
                    entity_type="GoLive_Date",
                    value=date_str,
                    confidence=0.85,
                    context=match.group(0),
                    source_field="content"
                )
        
        return None
    
    def extract_all_entities(self, text: str) -> List[EntityMatch]:
        """Extract all healthcare entities from text."""
        entities = []
        
        # Extract each entity type
        ehr_vendor = self.extract_ehr_vendor(text)
        if ehr_vendor:
            entities.append(ehr_vendor)
        
        lifecycle_phase = self.extract_ehr_lifecycle_phase(text)
        if lifecycle_phase:
            entities.append(lifecycle_phase)
        
        org_type = self.extract_organization_type(text)
        if org_type:
            entities.append(org_type)
        
        go_live_date = self.extract_go_live_date(text)
        if go_live_date:
            entities.append(go_live_date)
        
        return entities
    
    def normalize_organization_name(self, name: str) -> str:
        """Normalize organization name for deduplication."""
        # Remove common suffixes and prefixes
        name = re.sub(r'\b(inc|llc|ltd|corporation|corp|company|co|health|healthcare|medical|center|clinic|hospital|system)\b', '', name, flags=re.IGNORECASE)
        
        # Remove punctuation and extra whitespace
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name.lower()


# Global instance for easy access
entity_extractor = HealthcareEntityExtractor()
