import time
from fastapi import FastAPI
from pydantic import BaseModel
from src.flows.healthcare_flow import app_graph as healthcare_app, HCState
from src.flows.corporate_flow_stub import app as corporate_app, CorporateState
from src.flows.providers_flow_stub import app as providers_app, ProvidersState
from src.runtime.config import RunConfig
from src.runtime.batching import BatchConfig, create_batch_processor
from src.runtime.cache_layers import create_cache_stack, CacheStats
from src.runtime.tracing import create_tracing_manager, create_workflow_tracer, NoOpTracer
from src.runtime.budget import BudgetManager
from src.runtime.cache import DiskCache


class RunBody(BaseModel):
    segment: str
    targetcount: int = 50
    mode: str = "fast"
    region: str = "both"


app = FastAPI()
app.start_time = time.time()
config = RunConfig()

# Initialize Phase 4 components
budget = BudgetManager(config)
disk_cache = DiskCache(base_dir="cache", ttl_secs=config.cache_ttl)
cache_stack = create_cache_stack(disk_cache, memory_size=1000)
cache_stats = CacheStats()
tracing_manager = create_tracing_manager()
workflow_tracer = create_workflow_tracer(tracing_manager)


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
def metrics():
    """Prometheus-style metrics endpoint."""
    # This would typically collect metrics from a metrics collector
    # For now, return basic application metrics
    return {
        "application": {
            "name": "icp-discovery-engine",
            "version": "1.0.0",
            "uptime": time.time() - app.start_time if hasattr(app, 'start_time') else 0
        },
        "budget": {
            "max_searches": config.max_searches,
            "max_fetches": config.max_fetches,
            "max_enrich": config.max_enrich,
            "max_llm_tokens": config.max_llm_tokens
        },
        "cache": {
            "ttl_seconds": config.cache_ttl,
            "per_domain_cap": config.per_domain_cap
        }
    }

@app.get("/status")
def status():
    """Detailed application status."""
    allowlist_list = list(config.allowlist) if config.allowlist else []
    print(f"DEBUG: config.allowlist = {config.allowlist}")
    print(f"DEBUG: allowlist_list = {allowlist_list}")
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "run": "/run"
        },
        "configuration": {
            "mode": config.mode,
            "allowlist_domains": allowlist_list
        }
    }

@app.post("/run")
def run(body: RunBody):
    if body.segment not in ["healthcare", "corporate", "providers"]:
        return {"error": "Unsupported segment"}
    
    # Select appropriate state and app based on segment
    if body.segment == "healthcare":
        state = HCState(targetcount=body.targetcount, region=body.region, mode=body.mode)
        app = healthcare_app
        csv_file = "healthcare.csv"
    elif body.segment == "corporate":
        state = CorporateState(targetcount=body.targetcount, region=body.region, mode=body.mode)
        app = corporate_app
        csv_file = "corporate.csv"
    elif body.segment == "providers":
        state = ProvidersState(targetcount=body.targetcount, region=body.region, mode=body.mode)
        app = providers_app
        csv_file = "providers.csv"
    
    result = app.invoke(state)
    if isinstance(result, dict):
        outputs = result.get("outputs", [])
        budget = result.get("budget_snapshot") or result.get("budget")
        summary = result.get("summary")
    else:
        outputs = getattr(result, "outputs", [])
        budget = getattr(result, "budget_snapshot", None)
        summary = getattr(result, "summary", None)
    artifacts = getattr(result, "artifacts", None)
    # Fallback to runs/latest if artifacts missing
    if artifacts is None:
        from pathlib import Path as _P
        _latest = _P("runs") / "latest"
        _csv = _latest / csv_file
        _sum = _latest / "summary.txt"
        if _csv.exists() or _sum.exists():
            artifacts = {"csv": str(_csv) if _csv.exists() else None, "summary": str(_sum) if _sum.exists() else None}
    return {
        "segment": body.segment,
        "count": len(outputs),
        "outputs": outputs,
        "budget": budget,
        "summary": summary,
        "artifacts": artifacts,
        "message": "OK",
    }


@app.get("/batch/status")
def batch_status():
    """Get batch processing status."""
    return {
        "batch_processing": {
            "enabled": True,
            "checkpoint_dir": "checkpoints",
            "default_batch_size": 50
        }
    }


@app.get("/cache/stats")
def cache_stats_endpoint():
    """Get cache statistics."""
    return {
        "cache": {
            "layers": len(cache_stack.layers),
            "stats": cache_stats.get_stats()
        }
    }


@app.get("/tracing/status")
def tracing_status():
    """Get tracing status."""
    return {
        "tracing": {
            "enabled": not isinstance(tracing_manager.tracer, NoOpTracer),
            "service_name": tracing_manager.service_name,
            "endpoint": tracing_manager.endpoint
        }
    }


@app.get("/system/health")
def system_health():
    """Comprehensive system health check."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.time() - app.start_time if hasattr(app, 'start_time') else 0,
        "components": {
            "budget": {
                "searches_used": budget.searches,
                "fetches_used": budget.fetches,
                "enrich_used": budget.enrich,
                "llm_tokens_used": budget.llm_tokens
            },
            "cache": cache_stats.get_stats(),
            "tracing": {
                "enabled": not isinstance(tracing_manager.tracer, NoOpTracer)
            }
        }
    }


