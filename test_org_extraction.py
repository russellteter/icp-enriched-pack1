#!/usr/bin/env python3
"""
Test script for organization extraction from healthcare content
"""

from src.definitions.icp_definitions import extract_organizations_from_text, is_organization_name

# Test content that mentions multiple healthcare organizations
test_content_1 = """
Intermountain Health announced that their Epic go-live training program will begin next month. 
The health system's credentialed trainers will work with Mayo Clinic's implementation team 
to ensure a smooth transition. Cleveland Clinic has also shared their virtual training 
best practices with other hospital systems.
"""

test_content_2 = """
Becker's Hospital Review reports that several major health systems are implementing 
new EHR training programs. UCHealth recently completed their Epic implementation, 
while Kaiser Permanente continues to expand their virtual learning initiatives.
Northwell Health has partnered with training vendors to improve their VILT offerings.
"""

test_content_3 = """
Top 10 Best Healthcare Training Programs of 2024 includes innovative approaches 
from leading medical centers. The report covers virtual instructor-led training 
methodologies and implementation strategies for large health systems.
"""

print("=== Testing Organization Extraction ===\n")

print("Test 1 - Content with clear healthcare organizations:")
orgs1 = extract_organizations_from_text(test_content_1, "healthcare")
print(f"Extracted: {orgs1}")
for org in orgs1:
    print(f"  {org} -> Valid: {is_organization_name(org, 'healthcare')}")

print("\nTest 2 - News article mentioning organizations:")
orgs2 = extract_organizations_from_text(test_content_2, "healthcare")
print(f"Extracted: {orgs2}")
for org in orgs2:
    print(f"  {org} -> Valid: {is_organization_name(org, 'healthcare')}")

print("\nTest 3 - Article title (should extract few/no orgs):")
orgs3 = extract_organizations_from_text(test_content_3, "healthcare")
print(f"Extracted: {orgs3}")
for org in orgs3:
    print(f"  {org} -> Valid: {is_organization_name(org, 'healthcare')}")

print("\n=== Testing Known Examples ===")
known_examples = [
    "Intermountain Health",
    "Mayo Clinic",
    "Cleveland Clinic", 
    "Kaiser Permanente",
    "Becker's Hospital Review",
    "Top 10 Best Training Programs",
    "EHR Training Guide",
    "Walmart Academy"
]

for example in known_examples:
    is_valid = is_organization_name(example, "healthcare")
    print(f"{example:<30} -> Valid: {is_valid}")