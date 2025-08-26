import os
import httpx
import json
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib
import time
from pathlib import Path


class ExploriumClient:
    """Explorium API client for company enrichment"""
    
    def __init__(self):
        self.api_key = os.getenv("EXPLORIUM_API_KEY")
        self.base_url = "https://api.explorium.ai/v2"
        self.cache_dir = Path(".cache/explorium")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = 7 * 24 * 3600  # 7 days
        
    def _get_cache_path(self, company: str) -> Path:
        """Get cache file path for a company"""
        cache_key = hashlib.md5(company.lower().encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_from_cache(self, company: str) -> Optional[Dict]:
        """Load enrichment data from cache if available and not expired"""
        cache_path = self._get_cache_path(company)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                    if time.time() - cached_data.get('timestamp', 0) < self.cache_ttl:
                        print(f"Cache hit for company: {company}")
                        return cached_data.get('data', {})
            except Exception as e:
                print(f"Error loading cache for {company}: {e}")
        return None
    
    def _save_to_cache(self, company: str, data: Dict):
        """Save enrichment data to cache"""
        cache_path = self._get_cache_path(company)
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'company': company,
                    'data': data
                }, f)
        except Exception as e:
            print(f"Error saving cache for {company}: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def enrich_firmographics(self, company: str = None, domain: str = None) -> Dict:
        """
        Enrich company data using Explorium API
        
        Args:
            company: Company name
            domain: Company domain (optional)
        
        Returns:
            Dict with firmographic and technographic data
        """
        # Check cache first
        cache_key = company or domain or ""
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Return empty dict if no API key
        if not self.api_key:
            print("Warning: Explorium API key not configured")
            return {}
        
        try:
            # Prepare request payload
            payload = {}
            if company:
                payload['company_name'] = company
            if domain:
                payload['website'] = domain
            
            # Make API request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f'{self.base_url}/company/enrich',
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract key firmographic fields
                    enriched = {
                        # Size indicators
                        'Number of employees range all sites': data.get('employee_count_range', ''),
                        'employee_count': data.get('employee_count', 0),
                        'employee_range': data.get('employee_range', ''),
                        
                        # Revenue indicators  
                        'revenue_range': data.get('revenue_range', ''),
                        'annual_revenue': data.get('annual_revenue', 0),
                        
                        # Location data
                        'headquarters_country': data.get('country', ''),
                        'headquarters_city': data.get('city', ''),
                        'headquarters_state': data.get('state', ''),
                        'hq_location': f"{data.get('city', '')}, {data.get('state', '')}".strip(', '),
                        
                        # Industry/vertical
                        'industry': data.get('industry', ''),
                        'sub_industry': data.get('sub_industry', ''),
                        'sic_codes': data.get('sic_codes', []),
                        'naics_codes': data.get('naics_codes', []),
                        
                        # Company identifiers
                        'company_name': data.get('company_name', company),
                        'website': data.get('website', domain),
                        'linkedin_url': data.get('linkedin_url', ''),
                        
                        # Technology stack (technographics)
                        'technologies': data.get('technologies', []),
                        'has_lms': any('LMS' in tech or 'Learning Management' in tech 
                                      for tech in data.get('technologies', [])),
                        'has_video_conferencing': any(tech in ['Zoom', 'Microsoft Teams', 'WebEx', 'GoToMeeting'] 
                                                     for tech in data.get('technologies', [])),
                        
                        # Additional indicators
                        'is_fortune_500': data.get('is_fortune_500', False),
                        'is_global_2000': data.get('is_global_2000', False),
                        'number_of_locations': data.get('number_of_locations', 0),
                        
                        # Company type
                        'company_type': data.get('company_type', ''),
                        'ownership_type': data.get('ownership_type', ''),
                        
                        # Raw response for debugging
                        '_raw_response': data
                    }
                    
                    # Save to cache
                    self._save_to_cache(cache_key, enriched)
                    
                    print(f"Successfully enriched company: {company or domain}")
                    return enriched
                    
                elif response.status_code == 404:
                    print(f"Company not found in Explorium: {company or domain}")
                    return {}
                    
                elif response.status_code == 429:
                    print("Explorium API rate limit reached")
                    return {}
                    
                else:
                    print(f"Explorium API error: {response.status_code} - {response.text}")
                    return {}
                    
        except httpx.TimeoutException:
            print(f"Timeout enriching company: {company or domain}")
            return {}
            
        except Exception as e:
            print(f"Error enriching company {company or domain}: {e}")
            return {}
    
    def meets_size_requirements(self, enriched_data: Dict, min_employees: int) -> bool:
        """
        Check if company meets minimum size requirements
        
        Args:
            enriched_data: Data from enrich_firmographics
            min_employees: Minimum employee count required
        
        Returns:
            True if meets requirements, False otherwise
        """
        # Check various employee count fields
        employee_count = enriched_data.get('employee_count', 0)
        if employee_count >= min_employees:
            return True
        
        # Check employee range
        employee_range = enriched_data.get('Number of employees range all sites', '')
        if not employee_range:
            employee_range = enriched_data.get('employee_range', '')
        
        # Parse common range formats
        range_mappings = {
            '10001+': 10001,
            '5001-10000': 5001,
            '1001-5000': 1001,
            '501-1000': 501,
            '201-500': 201,
            '51-200': 51,
            '11-50': 11,
            '1-10': 1
        }
        
        for range_str, min_val in range_mappings.items():
            if range_str in employee_range:
                return min_val >= min_employees
        
        # Check Fortune/Global status for large company requirements
        if min_employees >= 7500:
            if enriched_data.get('is_fortune_500') or enriched_data.get('is_global_2000'):
                return True
        
        return False
    
    def get_region(self, enriched_data: Dict) -> str:
        """
        Determine region from enriched data
        
        Returns:
            'na' for North America, 'emea' for Europe/Middle East/Africa, 'apac' for Asia-Pacific
        """
        country = enriched_data.get('headquarters_country', '').upper()
        state = enriched_data.get('headquarters_state', '').upper()
        
        # North America
        na_countries = ['US', 'USA', 'UNITED STATES', 'CA', 'CANADA', 'MX', 'MEXICO']
        if country in na_countries or state in ['US', 'USA']:
            return 'na'
        
        # EMEA
        emea_countries = [
            'GB', 'UK', 'UNITED KINGDOM', 'FR', 'FRANCE', 'DE', 'GERMANY',
            'IT', 'ITALY', 'ES', 'SPAIN', 'NL', 'NETHERLANDS', 'BE', 'BELGIUM',
            'SE', 'SWEDEN', 'NO', 'NORWAY', 'DK', 'DENMARK', 'FI', 'FINLAND',
            'CH', 'SWITZERLAND', 'AT', 'AUSTRIA', 'PL', 'POLAND', 'IE', 'IRELAND',
            'AE', 'UAE', 'SA', 'SAUDI ARABIA', 'ZA', 'SOUTH AFRICA', 'IL', 'ISRAEL'
        ]
        if country in emea_countries:
            return 'emea'
        
        # Default to APAC for Asia-Pacific and other regions
        return 'apac'


