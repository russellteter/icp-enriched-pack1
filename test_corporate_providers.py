#!/usr/bin/env python3
"""
Test script for corporate and providers organization extraction
"""

from src.definitions.icp_definitions import extract_organizations_from_text, is_organization_name, get_icp_definition

# Test corporate academy content
corporate_content = """
Walmart Academy continues to expand its training programs for associates and managers.
The company's corporate university has partnered with McDonald's Hamburger University
to share best practices. Disney University also announced new virtual learning initiatives
for their global workforce. AT&T Academy launched innovative leadership development programs.
"""

# Test training provider content  
providers_content = """
Sandler Training announced new virtual instructor-led courses for enterprise clients.
Dale Carnegie Training has expanded their public schedule with 15 new sessions this quarter.
Global Knowledge offers certified training programs for corporate partners,
while Learning Tree International focuses on technology training for organizations.
Franklin Covey provides leadership development training with live online delivery.
"""

print("=== Testing Corporate Academy Extraction ===")
corp_orgs = extract_organizations_from_text(corporate_content, "corporate")
print(f"Extracted: {corp_orgs}")
for org in corp_orgs:
    print(f"  {org} -> Valid: {is_organization_name(org, 'corporate')}")

print("\n=== Testing Training Providers Extraction ===")
provider_orgs = extract_organizations_from_text(providers_content, "providers")
print(f"Extracted: {provider_orgs}")
for org in provider_orgs:
    print(f"  {org} -> Valid: {is_organization_name(org, 'providers')}")

print("\n=== Testing Known Examples ===")
corporate_examples = ["Walmart Academy", "McDonald's Hamburger University", "Disney University", "GE Crotonville"]
provider_examples = ["Sandler Training", "Dale Carnegie Training", "Global Knowledge", "Franklin Covey"]

print("\nCorporate Examples:")
for example in corporate_examples:
    is_valid = is_organization_name(example, "corporate")
    print(f"  {example:<35} -> Valid: {is_valid}")

print("\nProvider Examples:")  
for example in provider_examples:
    is_valid = is_organization_name(example, "providers")
    print(f"  {example:<35} -> Valid: {is_valid}")

print("\n=== ICP Definition Summary ===")
for segment in ["healthcare", "corporate", "providers"]:
    icp = get_icp_definition(segment)
    print(f"\n{segment.title()} ICP:")
    print(f"  Must-haves: {len(icp.get('must_haves', []))}")
    print(f"  Examples: {len(icp.get('example_organizations', []))}")
    print(f"  Search patterns: {len(icp.get('search_patterns', []))}")