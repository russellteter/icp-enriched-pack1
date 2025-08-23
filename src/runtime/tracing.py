"""OpenTelemetry tracing for distributed observability."""

import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from functools import wraps


class NoOpTracer:
    """No-op tracer when OpenTelemetry is not available."""
    
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        return NoOpSpan()
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        pass
    
    def set_attribute(self, key: str, value: Any):
        pass


class NoOpSpan:
    """No-op span when OpenTelemetry is not available."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def set_attribute(self, key: str, value: Any):
        pass
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        pass


class TracingManager:
    """Manages OpenTelemetry tracing."""
    
    def __init__(self, service_name: str = "icp-discovery-engine", 
                 endpoint: Optional[str] = None):
        self.service_name = service_name
        self.endpoint = endpoint
        self.tracer = self._setup_tracer()
    
    def _setup_tracer(self):
        """Setup OpenTelemetry tracer."""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource
            
            # Create tracer provider
            resource = Resource.create({"service.name": self.service_name})
            provider = TracerProvider(resource=resource)
            
            # Add span processor
            if self.endpoint:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=self.endpoint)
            else:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                exporter = ConsoleSpanExporter()
            
            provider.add_span_processor(BatchSpanProcessor(exporter))
            
            # Set global tracer provider
            trace.set_tracer_provider(provider)
            
            return trace.get_tracer(self.service_name)
            
        except ImportError:
            print("WARNING: OpenTelemetry not installed. Tracing disabled.")
            return NoOpTracer()
        except Exception as e:
            print(f"WARNING: Failed to setup tracing: {e}. Using no-op tracer.")
            return NoOpTracer()
    
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Start a new span."""
        return self.tracer.start_span(name, attributes=attributes)
    
    def trace_function(self, name: Optional[str] = None, 
                      attributes: Optional[Dict[str, Any]] = None):
        """Decorator to trace function execution."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"
                with self.start_span(span_name, attributes) as span:
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("function.success", True)
                        return result
                    except Exception as e:
                        span.set_attribute("function.success", False)
                        span.set_attribute("function.error", str(e))
                        raise
            return wrapper
        return decorator
    
    @contextmanager
    def trace_operation(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing operations."""
        with self.start_span(name, attributes) as span:
            try:
                yield span
            except Exception as e:
                span.set_attribute("operation.success", False)
                span.set_attribute("operation.error", str(e))
                raise


class WorkflowTracer:
    """Specialized tracer for workflow operations."""
    
    def __init__(self, tracing_manager: TracingManager):
        self.tracer = tracing_manager
    
    def trace_node(self, node_name: str, segment: str, region: str):
        """Trace a workflow node execution."""
        attributes = {
            "workflow.node": node_name,
            "workflow.segment": segment,
            "workflow.region": region,
            "workflow.timestamp": time.time()
        }
        return self.tracer.trace_operation(f"workflow.{node_name}", attributes)
    
    def trace_batch(self, batch_id: str, batch_size: int, batch_num: int):
        """Trace batch processing."""
        attributes = {
            "batch.id": batch_id,
            "batch.size": batch_size,
            "batch.number": batch_num,
            "batch.timestamp": time.time()
        }
        return self.tracer.trace_operation(f"batch.{batch_id}", attributes)
    
    def trace_cache_operation(self, operation: str, key: str, hit: bool):
        """Trace cache operations."""
        attributes = {
            "cache.operation": operation,
            "cache.key": key,
            "cache.hit": hit,
            "cache.timestamp": time.time()
        }
        return self.tracer.trace_operation(f"cache.{operation}", attributes)
    
    def trace_budget_check(self, budget_type: str, current: int, limit: int):
        """Trace budget checks."""
        attributes = {
            "budget.type": budget_type,
            "budget.current": current,
            "budget.limit": limit,
            "budget.percentage": (current / limit * 100) if limit > 0 else 0,
            "budget.timestamp": time.time()
        }
        return self.tracer.trace_operation(f"budget.{budget_type}", attributes)


def create_tracing_manager(service_name: str = "icp-discovery-engine",
                          endpoint: Optional[str] = None) -> TracingManager:
    """Factory function to create a tracing manager."""
    return TracingManager(service_name, endpoint)


def create_workflow_tracer(tracing_manager: TracingManager) -> WorkflowTracer:
    """Factory function to create a workflow tracer."""
    return WorkflowTracer(tracing_manager)
