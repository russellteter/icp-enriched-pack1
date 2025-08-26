"""
Structured API client for ICP Discovery Engine backend communication.
Provides robust error handling, retry logic, and typed responses.
"""

import requests
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import streamlit as st


class Segment(Enum):
    HEALTHCARE = "healthcare"
    CORPORATE = "corporate"
    PROVIDERS = "providers"


class Mode(Enum):
    FAST = "fast"
    DEEP = "deep"


class Region(Enum):
    NA = "na"
    EMEA = "emea"
    BOTH = "both"


@dataclass
class RunRequest:
    """Request model for workflow execution."""
    segment: Segment
    targetcount: int = 50
    mode: Mode = Mode.FAST
    region: Region = Region.BOTH


@dataclass
class WorkflowResult:
    """Response model for workflow execution results."""
    segment: str
    count: int
    outputs: List[Dict[str, Any]]
    budget: Optional[Dict[str, int]]
    summary: Optional[str]
    artifacts: Optional[Dict[str, str]]
    message: str
    execution_time: float = 0.0


@dataclass
class SystemHealth:
    """System health status model."""
    status: str
    timestamp: float
    uptime: float
    components: Dict[str, Any]


@dataclass
class ApiError:
    """API error response model."""
    status_code: int
    message: str
    details: Optional[str] = None


class ICPApiClient:
    """Structured API client for ICP Discovery Engine."""
    
    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """Make HTTP request with error handling and retries."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                    
                return False, {
                    "error": ApiError(
                        status_code=response.status_code,
                        message=error_msg,
                        details=error_detail
                    )
                }
                
        except requests.exceptions.ConnectionError:
            return False, {
                "error": ApiError(
                    status_code=0,
                    message="Connection Error",
                    details="Cannot connect to server. Ensure it's running on localhost:8080"
                )
            }
        except requests.exceptions.Timeout:
            return False, {
                "error": ApiError(
                    status_code=0,
                    message="Timeout Error",
                    details=f"Request timed out after {self.timeout} seconds"
                )
            }
        except Exception as e:
            return False, {
                "error": ApiError(
                    status_code=0,
                    message="Unexpected Error",
                    details=str(e)
                )
            }
    
    def health_check(self) -> Tuple[bool, SystemHealth]:
        """Check server health status."""
        success, data = self._make_request("GET", "/health")
        
        if success:
            return True, SystemHealth(
                status=data.get("status", "unknown"),
                timestamp=data.get("timestamp", time.time()),
                uptime=0,  # Basic health endpoint doesn't include uptime
                components={}
            )
        else:
            return False, data["error"]
    
    def system_health(self) -> Tuple[bool, SystemHealth]:
        """Get comprehensive system health information."""
        success, data = self._make_request("GET", "/system/health")
        
        if success:
            return True, SystemHealth(
                status=data.get("status", "unknown"),
                timestamp=data.get("timestamp", time.time()),
                uptime=data.get("uptime", 0),
                components=data.get("components", {})
            )
        else:
            return False, data["error"]
    
    def get_metrics(self) -> Tuple[bool, Dict[str, Any]]:
        """Get application metrics."""
        return self._make_request("GET", "/metrics")
    
    def get_status(self) -> Tuple[bool, Dict[str, Any]]:
        """Get detailed application status."""
        return self._make_request("GET", "/status")
    
    def get_monitoring_dashboard(self) -> Tuple[bool, Dict[str, Any]]:
        """Get comprehensive dashboard monitoring data."""
        return self._make_request("GET", "/monitoring/dashboard")
    
    def get_cache_stats(self) -> Tuple[bool, Dict[str, Any]]:
        """Get cache performance statistics."""
        return self._make_request("GET", "/cache/stats")
    
    def get_batch_status(self) -> Tuple[bool, Dict[str, Any]]:
        """Get batch processing status."""
        return self._make_request("GET", "/batch/status")
    
    def get_tracing_status(self) -> Tuple[bool, Dict[str, Any]]:
        """Get distributed tracing status."""
        return self._make_request("GET", "/tracing/status")
    
    def get_user_behavior_analytics(self, days: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """Get user behavior analytics."""
        return self._make_request("GET", f"/analytics/user-behavior?days={days}")
    
    def get_performance_trends(self, days: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """Get performance trends analytics."""
        return self._make_request("GET", f"/analytics/performance-trends?days={days}")
    
    def get_resource_utilization(self, days: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """Get resource utilization analytics."""
        return self._make_request("GET", f"/analytics/resource-utilization?days={days}")
    
    def get_comprehensive_analytics(self, days: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """Get comprehensive analytics data."""
        return self._make_request("GET", f"/analytics/comprehensive?days={days}")
    
    def export_analytics(self, days: int = 30, format: str = "csv") -> Tuple[bool, Dict[str, Any]]:
        """Export analytics data to specified format."""
        return self._make_request("POST", f"/export/analytics?days={days}&format={format}")
    
    def export_user_behavior(self, days: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """Export user behavior analytics to CSV."""
        return self._make_request("GET", f"/export/user-behavior?days={days}")
    
    def export_performance_trends(self, days: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """Export performance trends to CSV."""
        return self._make_request("GET", f"/export/performance-trends?days={days}")
    
    def export_management_report(self, days: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """Export management summary report."""
        return self._make_request("GET", f"/export/management-report?days={days}")
    
    def run_workflow(self, request: RunRequest) -> Tuple[bool, WorkflowResult]:
        """Execute ICP discovery workflow."""
        start_time = time.time()
        
        payload = {
            "segment": request.segment.value,
            "targetcount": request.targetcount,
            "mode": request.mode.value,
            "region": request.region.value
        }
        
        success, data = self._make_request("POST", "/run", json=payload)
        execution_time = time.time() - start_time
        
        if success:
            return True, WorkflowResult(
                segment=data.get("segment", ""),
                count=data.get("count", 0),
                outputs=data.get("outputs", []),
                budget=data.get("budget"),
                summary=data.get("summary"),
                artifacts=data.get("artifacts"),
                message=data.get("message", ""),
                execution_time=execution_time
            )
        else:
            return False, data["error"]


# Singleton instance for Streamlit
@st.cache_resource
def get_api_client() -> ICPApiClient:
    """Get cached API client instance."""
    return ICPApiClient()


# Helper functions for Streamlit components
def display_api_error(error: ApiError, context: str = ""):
    """Display API error in Streamlit with proper formatting."""
    if error.status_code == 0:
        st.error(f"🔌 {error.message}: {error.details}")
        if "Connection Error" in error.message:
            st.info("💡 To start the server, run: `make run` or `uvicorn src.server.app:app --host 0.0.0.0 --port 8080`")
    else:
        st.error(f"❌ {context} Error ({error.status_code}): {error.details}")


def format_budget_display(budget: Optional[Dict[str, int]]) -> Dict[str, str]:
    """Format budget data for display in Streamlit metrics."""
    if not budget:
        return {"Searches": "N/A", "Fetches": "N/A", "Enrichments": "N/A", "Tokens": "N/A"}
    
    return {
        "Searches": f"{budget.get('searches', 0)}",
        "Fetches": f"{budget.get('fetches', 0)}",  
        "Enrichments": f"{budget.get('enrich', 0)}",
        "Tokens": f"{budget.get('llm_tokens', 0):,}"
    }


def format_execution_time(seconds: float) -> str:
    """Format execution time for display."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"