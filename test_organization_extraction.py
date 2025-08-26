#!/usr/bin/env python3
"""
Test organization extraction across all three ICP segments
"""

from src.definitions.icp_definitions import extract_organizations_from_text, is_organization_name

# Test healthcare organization extraction
healthcare_content = """
Intermountain Health announced completion of its Epic EHR go-live training program.
The health system worked with Mayo Clinic on virtual instructor-led training for 
credentialed trainers. Cleveland Clinic shared their command center approach,
while Kaiser Permanente provided insights on super user training models.
Northwell Health implemented similar VILT programs for their Epic rollout.
"""

print("=== Testing Healthcare Organization Extraction ===")
healthcare_orgs = extract_organizations_from_text(healthcare_content, "healthcare")
print(f"Extracted organizations: {healthcare_orgs}")
for org in healthcare_orgs:
    is_valid = is_organization_name(org, "healthcare")
    print(f"  • {org:<30} -> Valid: {is_valid}")

print()

# Test corporate academy extraction  
corporate_content = """
Walmart Academy continues to expand its training programs for associates and managers.
The company's corporate university has partnered with McDonald's Hamburger University
to share best practices. Disney University also announced new virtual learning initiatives
for their global workforce. GE Crotonville launched innovative leadership development programs.
Target Learning Academy focuses on retail excellence training.
"""

print("=== Testing Corporate Academy Extraction ===")
corporate_orgs = extract_organizations_from_text(corporate_content, "corporate")
print(f"Extracted organizations: {corporate_orgs}")
for org in corporate_orgs:
    is_valid = is_organization_name(org, "corporate")
    print(f"  • {org:<30} -> Valid: {is_valid}")

print()

# Test training provider extraction
providers_content = """
Sandler Training announced new virtual instructor-led courses for enterprise clients.
Dale Carnegie Training has expanded their public schedule with 15 new sessions this quarter.
Global Knowledge offers certified training programs for corporate partners,
while Learning Tree International focuses on technology training for organizations.
Franklin Covey provides leadership development training with live online delivery.
New Horizons Learning Group specializes in IT training for businesses.
"""

print("=== Testing Training Providers Extraction ===")
providers_orgs = extract_organizations_from_text(providers_content, "providers")
print(f"Extracted organizations: {providers_orgs}")
for org in providers_orgs:
    is_valid = is_organization_name(org, "providers")
    print(f"  • {org:<30} -> Valid: {is_valid}")

print()
print("=== Test Summary ===")
print(f"Healthcare: {len(healthcare_orgs)} organizations extracted")
print(f"Corporate: {len(corporate_orgs)} organizations extracted")
print(f"Providers: {len(providers_orgs)} organizations extracted")
print(f"Total: {len(healthcare_orgs) + len(corporate_orgs) + len(providers_orgs)} organizations")