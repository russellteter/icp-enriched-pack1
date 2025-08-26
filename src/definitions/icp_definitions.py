"""
ICP (Ideal Customer Profile) Definitions
Structured definitions for each target segment with must-haves, disqualifiers, and search patterns
"""

HEALTHCARE_ICP = {
    "name": "Healthcare EHR Implementation & Training",
    "must_haves": [
        "Provider organization (hospital, health system, medical center, clinic network)",
        "Active EHR lifecycle (selection, implementation, go-live, optimization)",
        "VILT (Virtual Instructor-Led Training) as primary training modality",
        "Training infrastructure (super users, credentialed trainers, command center)"
    ],
    "nice_to_haves": [
        "Multi-facility health system",
        "10,000+ employees",
        "Recent Epic or Cerner implementation",
        "Named training programs"
    ],
    "disqualifiers": [
        "Payers/insurance companies",
        "Pharmaceutical companies", 
        "Medical device manufacturers",
        "Async-only training",
        "Single department pilots",
        "Micro practices (<50 employees)",
        "Vendors/consultants (not providers)"
    ],
    "search_patterns": [
        "hospital", "health system", "medical center", "healthcare provider",
        "clinic", "health network", "healthcare organization", "IDN",
        "academic medical center", "AMC", "integrated delivery network"
    ],
    "evidence_keywords": [
        "epic go-live", "cerner implementation", "ehr training",
        "super users", "credentialed trainers", "command center",
        "virtual training", "vilt", "live online training",
        "zoom training", "teams training", "webex training"
    ],
    "example_organizations": [
        "Intermountain Health",
        "Mayo Clinic", 
        "Cleveland Clinic",
        "Kaiser Permanente",
        "Northwell Health",
        "Advocate Aurora Health",
        "Providence St. Joseph Health",
        "Sutter Health",
        "UCHealth",
        "Atrium Health"
    ]
}

CORPORATE_ICP = {
    "name": "Corporate Academy (Large Enterprise)",
    "must_haves": [
        "Named corporate academy or university",
        "Company size ≥7,500 employees OR Fortune 2000",
        "VILT modality documented (virtual classroom)",
        "Programmatic cohorts/learning paths",
        "Evidence of academy operations/staff"
    ],
    "nice_to_haves": [
        "Awards/recognition (Training Top 125, CLO Awards, ATD BEST)",
        "External scope (partners, dealers, customers)",
        "Multiple learning modalities",
        "Global reach",
        "Named Dean or Chief Learning Officer"
    ],
    "disqualifiers": [
        "Compliance-only L&D",
        "Customer-only academies (no employee focus)",
        "Higher education institutions",
        "Government schools/academies",
        "Training vendor academies",
        "Small companies (<7,500 employees)"
    ],
    "search_patterns": [
        "corporate university", "corporate academy", "learning center",
        "training academy", "employee university", "company university",
        "learning institute", "development academy", "talent academy"
    ],
    "evidence_keywords": [
        "virtual classroom", "vilt", "live online",
        "cohort", "learning path", "curriculum",
        "dean of", "chief learning officer", "academy director",
        "employee development", "leadership academy", "onboarding program"
    ],
    "example_organizations": [
        "Walmart Academy",
        "McDonald's Hamburger University",
        "Disney University",
        "GE Crotonville",
        "Deloitte University",
        "Amazon Career Choice",
        "AT&T University",
        "Bank of America Academy",
        "Home Depot's Store Support Center",
        "Target Learning & Development"
    ]
}

PROVIDERS_ICP = {
    "name": "Professional Training Providers (VILT-Core)",
    "must_haves": [
        "B2B business model (training for organizations)",
        "Live virtual training as core offering",
        "Public calendar with ≥5 sessions per 90 days",
        "Instructor bench with ≥5 instructors",
        "Professional accreditations (PMI, CompTIA, NEBOSH, etc.)"
    ],
    "nice_to_haves": [
        "Enterprise client logos/case studies",
        "Custom corporate training offerings",
        "Multi-region coverage (NA + EMEA)",
        "Industry specializations",
        "Blended learning options"
    ],
    "disqualifiers": [
        "MOOC platforms (Coursera, Udemy, edX)",
        "K-12 or test prep focus",
        "Async-only delivery",
        "Micro bootcamps (<3 months)",
        "Consulting as primary business",
        "Individual/consumer focus only",
        "Marketplace aggregators"
    ],
    "search_patterns": [
        "training provider", "training company", "learning provider",
        "corporate training", "professional training", "enterprise training",
        "authorized training partner", "certified training", "vilt provider"
    ],
    "evidence_keywords": [
        "virtual instructor-led", "live online training", "vilt",
        "public schedule", "open enrollment", "training calendar",
        "certified instructor", "authorized trainer", "accredited training",
        "corporate clients", "enterprise training", "custom training"
    ],
    "example_organizations": [
        "Sandler Training",
        "Dale Carnegie Training",
        "Franklin Covey",
        "New Horizons",
        "Global Knowledge",
        "Learning Tree International",
        "ExecuTrain",
        "AMA (American Management Association)",
        "Skillsoft",
        "CrossKnowledge"
    ]
}

def get_icp_definition(segment: str) -> dict:
    """Get ICP definition by segment name"""
    definitions = {
        "healthcare": HEALTHCARE_ICP,
        "corporate": CORPORATE_ICP,
        "providers": PROVIDERS_ICP
    }
    return definitions.get(segment.lower(), {})

def is_organization_name(text: str, segment: str) -> bool:
    """Check if text appears to be an organization name vs article title"""
    text_lower = text.lower()
    
    # Common article title patterns to exclude
    article_patterns = [
        "top ", "best ", "list of", "guide to", "how to",
        "why ", "what ", "when ", "where ", "report",
        "announces", "launches", "implements", "news"
    ]
    
    if any(pattern in text_lower for pattern in article_patterns):
        return False
    
    # Check for segment-specific patterns
    icp = get_icp_definition(segment)
    if icp:
        # Check if it contains any search patterns
        for pattern in icp.get("search_patterns", []):
            if pattern in text_lower:
                return True
    
    # Check if it's a known example
    for example in icp.get("example_organizations", []):
        if example.lower() in text_lower:
            return True
    
    return False

def extract_organizations_from_text(text: str, segment: str) -> list:
    """Extract potential organization names from text content"""
    import re
    
    organizations = []
    icp = get_icp_definition(segment)
    
    if not icp:
        return organizations
    
    # Patterns for finding organization names in text
    if segment == "healthcare":
        patterns = [
            # Pattern 1: "Intermountain Health", "Mayo Clinic", etc.
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Health|Hospital|Medical|Clinic|Healthcare)(?:\s+(?:System|Center|Network|Group))?\b',
            # Pattern 2: "at/for/with Organization"
            r'\b(?:at|for|with|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Health|Hospital|Medical|Clinic)(?:\s+(?:System|Center|Network|Group))?)\b',
            # Pattern 3: Organizations that implement systems
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Health|Hospital|Medical|Clinic)(?:\s+(?:System|Center|Network|Group))?)\s+(?:implements|launched|completed|announced)',
            # Pattern 4: Possessive forms "Mayo's Epic", "Cleveland's implementation"
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Health|Hospital|Medical|Clinic)(?:\s+(?:System|Center|Network|Group))?)?)\'s\s+(?:Epic|implementation|training)',
            # Pattern 5: Direct mentions in context
            r'\b([A-Z][a-z]+\s+(?:Health|Hospital|Medical|Clinic)(?:\s+(?:System|Center|Network|Group))?)\b',
        ]
    elif segment == "corporate":
        patterns = [
            # Pattern 1: "Walmart Academy", "Disney University"
            r'\b([A-Z][a-zA-Z\']+(?:\s+[A-Z][a-zA-Z\']+)*)\s+(?:Academy|University|Learning Center|Institute)\b',
            # Pattern 2: "McDonald's Hamburger University" (possessive)
            r'\b([A-Z][a-zA-Z\']+(?:\s+[A-Z][a-zA-Z\']+)*\'s\s+[A-Z][a-z]+\s+University)\b',
            # Pattern 3: "GE Crotonville" (specific corporate training centers)
            r'\b([A-Z]+\s+[A-Z][a-z]+)\b(?=\s+(?:announced|launched|expanded|continues))',
            # Pattern 4: Company mentions with academy context
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Academy|University)\b',
        ]
    elif segment == "providers":
        patterns = [
            # Pattern 1: "Sandler Training", "Dale Carnegie Training"
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Training)\b',
            # Pattern 2: "Global Knowledge", "Learning Tree International"
            r'\b([A-Z][a-z]+\s+(?:Knowledge|Learning|Tree)(?:\s+[A-Z][a-z]+)*)\b',
            # Pattern 3: "Franklin Covey" and similar provider names
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b(?=\s+(?:provides|offers|announced|focuses))',
            # Pattern 4: Training companies with "Academy" or "Institute"
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Academy|Institute)\b(?=.*training)',
        ]
    else:
        return organizations
    
    # Extract using patterns
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            
            # Clean and validate
            org_name = match.strip()
            if len(org_name) > 3 and is_organization_name(org_name, segment):
                organizations.append(org_name)
    
    # Deduplicate
    seen = set()
    unique_orgs = []
    for org in organizations:
        org_lower = org.lower()
        if org_lower not in seen:
            seen.add(org_lower)
            unique_orgs.append(org)
    
    return unique_orgs

def validate_against_icp(org_data: dict, segment: str) -> dict:
    """Validate an organization against ICP criteria"""
    icp = get_icp_definition(segment)
    if not icp:
        return {"valid": False, "reason": "Unknown segment"}
    
    # Check disqualifiers
    org_text = str(org_data).lower()
    for disqualifier in icp.get("disqualifiers", []):
        if disqualifier.lower() in org_text:
            return {
                "valid": False,
                "reason": f"Disqualified: {disqualifier}",
                "disqualifier": disqualifier
            }
    
    # Check must-haves (placeholder for future implementation)
    missing_must_haves = []
    # TODO: Implement sophisticated checking based on actual data
    # For now, assume validation is done elsewhere in the pipeline
    
    return {
        "valid": True,
        "missing_must_haves": missing_must_haves,
        "confidence": 0  # To be calculated based on evidence
    }