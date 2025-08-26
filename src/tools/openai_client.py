import os
import json
import hashlib
import time
from typing import Dict, Optional, List
from pathlib import Path
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from src.runtime.budget import BudgetManager, BudgetExceeded


class TokenSafeGPTClient:
    """Token-safe OpenAI client with caching and budget enforcement"""
    
    def __init__(self, budget_manager: BudgetManager):
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.budget_manager = budget_manager
        self.cache_dir = Path(".cache/gpt")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = 7 * 24 * 3600  # 7 days
        # Raise token and timeout limits to allow stronger reasoning/extraction
        self.max_tokens_per_call = 800
        self.timeout = 15  # seconds

        # Model routing (configurable via env)
        self.extraction_model = os.getenv("OPENAI_EXTRACTION_MODEL", "gpt-4o-mini")
        self.adjudication_model = os.getenv("OPENAI_ADJUDICATION_MODEL", "gpt-4o")
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)
    
    def _get_cache_path(self, prompt: str, context: str = "") -> Path:
        """Get cache file path for prompt+context combination"""
        cache_key = hashlib.md5(f"{prompt}|{context}".encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_from_cache(self, prompt: str, context: str = "") -> Optional[Dict]:
        """Load GPT response from cache if available and not expired"""
        cache_path = self._get_cache_path(prompt, context)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                    if time.time() - cached_data.get('timestamp', 0) < self.cache_ttl:
                        print(f"GPT cache hit for prompt hash: {cache_path.stem[:8]}")
                        return cached_data.get('response', {})
            except Exception as e:
                print(f"Error loading GPT cache: {e}")
        return None
    
    def _save_to_cache(self, prompt: str, context: str, response: Dict):
        """Save GPT response to cache"""
        cache_path = self._get_cache_path(prompt, context)
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'prompt': prompt[:100],  # Only save first 100 chars for debugging
                    'response': response
                }, f)
        except Exception as e:
            print(f"Error saving GPT cache: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)"""
        return len(text) // 4
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=3))
    def _make_request(self, messages: List[Dict], max_tokens: int = 150, model: Optional[str] = None, response_format: Optional[Dict] = None) -> Dict:
        """Make actual OpenAI API request with retry logic"""
        if not self.client:
            raise Exception("OpenAI client not initialized - check API key")
        
        response = self.client.chat.completions.create(
            model=(model or self.extraction_model),
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,  # Low temperature for consistent extraction
            timeout=self.timeout,
            response_format=response_format
        )
        
        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens,
            "model": response.model
        }
    
    def canonicalize_organization_name(self, title: str, url: str = "", icp_type: str = "") -> Dict:
        """
        GPT helper #1: Canonicalize organization name from noisy titles/snippets
        Per PRD: ≤300 tokens, cached for 7 days
        """
        # Check cache first
        context = f"{title}|{url}|{icp_type}"
        cached = self._load_from_cache("canonicalize_org", context)
        if cached:
            return cached
        
        # Build ICP-aware prompt
        if icp_type == "healthcare":
            context_hint = "Extract the HOSPITAL/HEALTH SYSTEM name that provides patient care, not the publication or website name. Look for: hospitals, health systems, medical centers, clinics."
        elif icp_type == "corporate":
            context_hint = "Extract the COMPANY name that has the corporate academy/university, not the LMS vendor or training provider."
        elif icp_type == "providers":
            context_hint = "Extract the TRAINING COMPANY name that provides courses, not their client companies."
        else:
            context_hint = "Extract the clean organization name."
        
        prompt = f"{context_hint} Title: '{title}' URL: {url}. If this is a news article ABOUT organizations, return 'ARTICLE_ABOUT_ORGS'. Otherwise return only the organization name."
        estimated_tokens = self._estimate_tokens(prompt) + 80
        
        if estimated_tokens > self.max_tokens_per_call:
            # Truncate title if too long
            title = title[:200]
            prompt = f"{context_hint} Title: '{title}'. Return organization name only."
            estimated_tokens = self._estimate_tokens(prompt) + 80
        
        # Check budget
        self.budget_manager.assert_can_use_tokens(estimated_tokens)
        
        try:
            response = self._make_request([
                {"role": "system", "content": f"You extract clean organization names for {icp_type} ICP matching. Return only the organization name or 'ARTICLE_ABOUT_ORGS'."},
                {"role": "user", "content": prompt}
            ], max_tokens=60, model=self.extraction_model)
            
            self.budget_manager.tick_tokens(response["tokens_used"])
            
            result = {
                "organization_name": response["content"].strip(),
                "tokens_used": response["tokens_used"]
            }
            
            # Cache result
            self._save_to_cache("canonicalize_org", context, result)
            return result
            
        except Exception as e:
            print(f"GPT canonicalization failed: {e}")
            # Return fallback
            return {"organization_name": title.split(" - ")[0][:100], "tokens_used": 0}
    
    def adjudicate_evidence(self, text: str, url: str, icp_type: str, must_haves: List[str]) -> Dict:
        """
        GPT helper #2: Evidence adjudication - Confirmed vs Probable
        Per PRD: ≤300 tokens, cached for 7 days, provider/corporate pages only
        """
        # Check cache first
        context = f"{url}|{icp_type}|{','.join(must_haves)}"
        cached = self._load_from_cache("adjudicate_evidence", context)
        if cached:
            return cached
        
        # Build ICP-specific prompt
        if icp_type == "healthcare":
            criteria = "active EHR lifecycle (implementation/go-live/optimization) AND VILT training present"
        elif icp_type == "corporate":
            criteria = "named corporate academy/university AND size ≥7,500 employees AND VILT modality"
        elif icp_type == "providers":
            criteria = "B2B training focus AND VILT core offering AND public calendar ≥5/90d AND instructor bench ≥5"
        else:
            criteria = "meets ICP requirements"
        
        prompt = f"Analyze this {icp_type} organization page for: {criteria}. Text: '{text[:500]}' Missing: {must_haves}. Return JSON with: meets_must_haves (true/false), summary (1 sentence), what_to_confirm_next (if probable)."
        
        estimated_tokens = self._estimate_tokens(prompt) + 100
        
        # Truncate if needed
        if estimated_tokens > self.max_tokens_per_call:
            text = text[:300]
            prompt = f"Check {icp_type} criteria: {criteria}. Text: '{text}'. Return JSON: {{\"meets_must_haves\": true/false, \"summary\": \"1 sentence\", \"what_to_confirm_next\": \"if needed\"}}"
            estimated_tokens = self._estimate_tokens(prompt) + 100
        
        # Check budget
        self.budget_manager.assert_can_use_tokens(estimated_tokens)
        
        try:
            response = self._make_request([
                {"role": "system", "content": f"You analyze {icp_type} organizations for ICP compliance. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ], max_tokens=150, model=self.adjudication_model, response_format={"type": "json_object"})
            
            self.budget_manager.tick_tokens(response["tokens_used"])
            
            # Parse JSON response
            try:
                parsed = json.loads(response["content"])
                result = {
                    "meets_must_haves": parsed.get("meets_must_haves", False),
                    "missing": must_haves if not parsed.get("meets_must_haves", False) else [],
                    "summary": parsed.get("summary", ""),
                    "what_to_confirm_next": parsed.get("what_to_confirm_next", ""),
                    "tokens_used": response["tokens_used"]
                }
            except json.JSONDecodeError:
                # Fallback parsing
                content = response["content"].lower()
                result = {
                    "meets_must_haves": "true" in content and "meets" in content,
                    "missing": must_haves,
                    "summary": response["content"][:100],
                    "what_to_confirm_next": "Manual review required",
                    "tokens_used": response["tokens_used"]
                }
            
            # Cache result
            self._save_to_cache("adjudicate_evidence", context, result)
            return result
            
        except Exception as e:
            print(f"GPT adjudication failed: {e}")
            # Return conservative fallback
            return {
                "meets_must_haves": False,
                "missing": must_haves,
                "summary": "GPT analysis failed",
                "what_to_confirm_next": "Manual verification required",
                "tokens_used": 0
            }
    
    def extract_targeted_data(self, text: str, extraction_type: str, icp_type: str) -> Dict:
        """
        GPT helper #3: Targeted extraction for specific fields
        Per PRD: ≤300 tokens, single page only
        """
        # Check cache first
        context = f"{extraction_type}|{icp_type}|{hashlib.md5(text.encode()).hexdigest()[:16]}"
        cached = self._load_from_cache("extract_targeted", context)
        if cached:
            return cached
        
        # Define extraction prompts by type
        if extraction_type == "healthcare_ehr":
            prompt = f"Extract from this healthcare text: EHR vendor, lifecycle phase, go-live date. Text: '{text[:400]}'. Return JSON: {{\"ehr_vendor\": \"\", \"lifecycle_phase\": \"\", \"golive_date\": \"\"}}"
        elif extraction_type == "corporate_academy":
            prompt = f"Extract academy info: academy name, academy URL. Text: '{text[:400]}'. Return JSON: {{\"academy_name\": \"\", \"academy_url\": \"\"}}"
        elif extraction_type == "providers_vilt":
            prompt = f"Extract VILT data: schedule URL, sessions in 90 days. Text: '{text[:400]}'. Return JSON: {{\"vilt_schedule_url\": \"\", \"vilt_sessions_90d\": 0}}"
        elif extraction_type == "providers_instructors":
            prompt = f"Extract instructor data: accreditations, instructor count. Text: '{text[:400]}'. Return JSON: {{\"accreditations\": [], \"instructor_bench_count\": 0}}"
        else:
            return {"error": "Unknown extraction type", "tokens_used": 0}
        
        estimated_tokens = self._estimate_tokens(prompt) + 80
        
        # Check budget
        if estimated_tokens > self.max_tokens_per_call:
            return {"error": "Text too long", "tokens_used": 0}
        
        self.budget_manager.assert_can_use_tokens(estimated_tokens)
        
        try:
            response = self._make_request([
                {"role": "system", "content": f"Extract specific {icp_type} data. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ], max_tokens=100, model=self.extraction_model, response_format={"type": "json_object"})
            
            self.budget_manager.tick_tokens(response["tokens_used"])
            
            # Parse JSON response
            try:
                parsed = json.loads(response["content"])
                result = {**parsed, "tokens_used": response["tokens_used"]}
            except json.JSONDecodeError:
                result = {"raw_response": response["content"], "tokens_used": response["tokens_used"]}
            
            # Cache result
            self._save_to_cache("extract_targeted", context, result)
            return result
            
        except Exception as e:
            print(f"GPT extraction failed: {e}")
            return {"error": str(e), "tokens_used": 0}
    
    def generate_next_steps(self, tier: str, missing: List[str], icp_type: str) -> str:
        """
        GPT helper #4: Generate "what to confirm next" for Probable rows
        Per PRD: ≤300 tokens, cached
        """
        if tier != "Probable" or not missing:
            return ""
        
        # Check cache first
        context = f"{icp_type}|{','.join(missing)}"
        cached = self._load_from_cache("next_steps", context)
        if cached and isinstance(cached, dict):
            return cached.get("next_step", "")
        
        prompt = f"Generate a specific 'what to confirm next' action for a Probable {icp_type} organization missing: {', '.join(missing)}. Return one actionable sentence."
        
        estimated_tokens = self._estimate_tokens(prompt) + 40
        
        # Check budget
        self.budget_manager.assert_can_use_tokens(estimated_tokens)
        
        try:
            response = self._make_request([
                {"role": "system", "content": f"Generate specific next steps for {icp_type} lead qualification."},
                {"role": "user", "content": prompt}
            ], max_tokens=50, model=self.extraction_model)
            
            self.budget_manager.tick_tokens(response["tokens_used"])
            
            result = {"next_step": response["content"].strip(), "tokens_used": response["tokens_used"]}
            
            # Cache result
            self._save_to_cache("next_steps", context, result)
            return result["next_step"]
            
        except Exception as e:
            print(f"GPT next steps failed: {e}")
            # Return fallback based on ICP and missing items
            if icp_type == "healthcare" and "vilt_present" in missing:
                return "Locate virtual training or VILT program on provider domain"
            elif icp_type == "corporate" and "named_academy" in missing:
                return "Find corporate academy/university name on company domain"
            elif icp_type == "providers" and "public_calendar" in missing:
                return "Locate public training schedule with ≥5 sessions in next 90 days"
            else:
                return "Manual verification required for missing requirements"
    
    def get_budget_usage(self) -> Dict:
        """Get current GPT token usage from budget manager"""
        if hasattr(self.budget_manager, 'llm_tokens'):
            return {
                "tokens_used": self.budget_manager.llm_tokens,
                "tokens_remaining": self.budget_manager.cfg.max_llm_tokens - self.budget_manager.llm_tokens,
                "budget_max": self.budget_manager.cfg.max_llm_tokens
            }
        return {"tokens_used": 0, "tokens_remaining": 0, "budget_max": 0}