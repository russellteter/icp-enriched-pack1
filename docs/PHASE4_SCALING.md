# Phase 4: Scaling & Optimization

This document describes the scaling and optimization features implemented in Phase 4 of the ICP Discovery Engine.

## Overview

Phase 4 introduces advanced scaling capabilities including:
- **Batching & Checkpointing**: Process large datasets in chunks with resume capability
- **Multi-layer Caching**: Memory, disk, and Redis caching layers
- **Distributed Tracing**: OpenTelemetry integration for observability
- **Enhanced Monitoring**: Comprehensive health checks and metrics

## Architecture

### Batching & Checkpointing

The batching system allows processing large datasets in manageable chunks with automatic checkpointing for fault tolerance.

```python
from src.runtime.batching import BatchConfig, create_batch_processor

# Configure batch processing
config = BatchConfig(
    batch_size=50,
    checkpoint_interval=10,
    checkpoint_dir="checkpoints",
    resume_from="checkpoint_batch_123_456789.json"  # Optional resume
)

# Create batch processor
processor = create_batch_processor(config, budget)

# Process items in batches
for batch_results in processor.process_batches(items, processor_func):
    # Process batch results
    pass
```

**Features:**
- Configurable batch sizes
- Automatic checkpointing every N batches
- Resume from any checkpoint
- Error handling with checkpoint preservation
- Progress tracking and statistics

### Multi-layer Caching

The caching system provides three layers of caching for optimal performance:

1. **L1: Memory Cache** (Fastest)
   - In-memory storage with LRU eviction
   - Configurable size limits
   - Automatic TTL support

2. **L2: Disk Cache** (Persistent)
   - File-based storage with TTL
   - SHA256 hashed keys
   - Automatic cleanup of expired entries

3. **L3: Redis Cache** (Distributed)
   - Optional Redis integration
   - JSON serialization
   - Graceful fallback if Redis unavailable

```python
from src.runtime.cache_layers import create_cache_stack

# Create cache stack
cache_stack = create_cache_stack(
    disk_cache=disk_cache,
    memory_size=1000,
    redis_url="redis://localhost:6379"  # Optional
)

# Use cache
value = cache_stack.get("key")
cache_stack.set("key", value, ttl=3600)
```

### Distributed Tracing

OpenTelemetry integration provides comprehensive tracing for debugging and performance analysis.

```python
from src.runtime.tracing import create_tracing_manager, create_workflow_tracer

# Setup tracing
tracing_manager = create_tracing_manager(
    service_name="icp-discovery-engine",
    endpoint="http://localhost:4317"  # Optional OTLP endpoint
)

workflow_tracer = create_workflow_tracer(tracing_manager)

# Trace operations
with workflow_tracer.trace_node("harvest", "healthcare", "na"):
    # Node execution
    pass

with workflow_tracer.trace_batch("batch_123", 50, 1):
    # Batch processing
    pass
```

**Features:**
- Automatic span creation for workflow nodes
- Batch processing traces
- Cache operation traces
- Budget monitoring traces
- Graceful fallback when OpenTelemetry unavailable

## API Endpoints

### New Phase 4 Endpoints

#### `/batch/status`
Get batch processing configuration and status.

```json
{
  "batch_processing": {
    "enabled": true,
    "checkpoint_dir": "checkpoints",
    "default_batch_size": 50
  }
}
```

#### `/cache/stats`
Get cache performance statistics.

```json
{
  "cache": {
    "layers": 2,
    "stats": {
      "hits": 150,
      "misses": 25,
      "sets": 175,
      "deletes": 5,
      "total_requests": 175,
      "hit_rate_percent": 85.71
    }
  }
}
```

#### `/tracing/status`
Get tracing configuration and status.

```json
{
  "tracing": {
    "enabled": true,
    "service_name": "icp-discovery-engine",
    "endpoint": "http://localhost:4317"
  }
}
```

#### `/system/health`
Comprehensive system health check including all components.

```json
{
  "status": "healthy",
  "timestamp": 1755917121.2384691,
  "uptime": 1.6221246719360352,
  "components": {
    "budget": {
      "searches_used": 0,
      "fetches_used": 0,
      "enrich_used": 0,
      "llm_tokens_used": 0
    },
    "cache": {
      "hits": 0,
      "misses": 0,
      "sets": 0,
      "deletes": 0,
      "total_requests": 0,
      "hit_rate_percent": 0
    },
    "tracing": {
      "enabled": false
    }
  }
}
```

## Configuration

### Environment Variables

Add these to your `.env` file for Phase 4 features:

```bash
# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379

# OpenTelemetry Configuration (Optional)
OTEL_ENDPOINT=http://localhost:4317

# Batch Processing
BATCH_SIZE=50
CHECKPOINT_INTERVAL=10

# Cache Configuration
MEMORY_CACHE_SIZE=1000
```

### Dependencies

Phase 4 adds these optional dependencies:

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install specific components
pip install redis  # For Redis caching
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp  # For tracing
```

## Makefile Commands

New Phase 4 commands added to the Makefile:

```bash
# Cache monitoring
make cache-stats

# Tracing status
make tracing-status

# System health
make system-health

# Batch processing status
make batch-status

# Development utilities
make clean          # Clean cache and temporary files
make dev-setup      # Setup development environment
make install-deps   # Install dependencies
```

## Usage Examples

### Batch Processing

```python
from src.runtime.batching import BatchConfig, create_batch_processor
from src.runtime.budget import BudgetManager

# Setup
config = BatchConfig(batch_size=25, checkpoint_interval=5)
budget = BudgetManager(run_config)
processor = create_batch_processor(config, budget)

# Process large dataset
large_dataset = [...]  # 1000+ items
for batch_results in processor.process_batches(large_dataset, process_function):
    print(f"Processed batch: {len(batch_results)} items")
    
# Resume from checkpoint
resume_config = BatchConfig(resume_from="checkpoint_batch_123_456789.json")
processor = create_batch_processor(resume_config, budget)
```

### Caching

```python
from src.runtime.cache_layers import create_cache_stack, CacheStats

# Setup cache with statistics
cache_stack = create_cache_stack(disk_cache, memory_size=500)
cache_stats = CacheStats()

# Use cache with statistics
key = "search_results_healthcare"
results = cache_stack.get(key)
if results is None:
    cache_stats.miss()
    results = expensive_operation()
    cache_stack.set(key, results, ttl=3600)
    cache_stats.set()
else:
    cache_stats.hit()

print(f"Cache hit rate: {cache_stats.get_stats()['hit_rate_percent']}%")
```

### Tracing

```python
from src.runtime.tracing import create_tracing_manager

# Setup tracing
tracing_manager = create_tracing_manager(
    service_name="icp-discovery-engine",
    endpoint="http://localhost:4317"
)

# Trace function execution
@tracing_manager.trace_function(attributes={"component": "search"})
def search_organizations(query: str):
    # Function implementation
    pass

# Trace operations
with tracing_manager.trace_operation("web_fetch", {"url": url}) as span:
    span.set_attribute("domain", domain)
    result = fetch_url(url)
    span.set_attribute("status_code", result.status_code)
```

## Monitoring & Observability

### Metrics Collection

The system provides comprehensive metrics through the API endpoints:

- **Budget Usage**: Track API call consumption
- **Cache Performance**: Hit rates and operation counts
- **Processing Progress**: Batch completion and error rates
- **System Health**: Uptime and component status

### Logging

Structured logging with context:

```python
from src.logging import get_logger

logger = get_logger("workflow", batch_id="batch_123", segment="healthcare")
logger.info("Processing batch", extra={
    "batch_size": 50,
    "budget_remaining": budget.searches
})
```

### Tracing

Distributed tracing provides:
- Request flow visualization
- Performance bottleneck identification
- Error correlation across services
- Dependency mapping

## Performance Optimization

### Caching Strategy

1. **Memory Cache**: Hot data for immediate access
2. **Disk Cache**: Persistent storage for repeated queries
3. **Redis Cache**: Shared cache for distributed deployments

### Batch Processing Benefits

- **Memory Efficiency**: Process large datasets without memory overflow
- **Fault Tolerance**: Resume from any checkpoint
- **Progress Tracking**: Real-time progress monitoring
- **Resource Management**: Controlled resource consumption

### Tracing Benefits

- **Performance Analysis**: Identify slow operations
- **Debugging**: Trace request flows across components
- **Monitoring**: Real-time system health and performance
- **Optimization**: Data-driven performance improvements

## Deployment Considerations

### Production Setup

1. **Redis**: Configure Redis for distributed caching
2. **OpenTelemetry**: Setup OTLP collector for tracing
3. **Monitoring**: Configure alerting on health endpoints
4. **Checkpoints**: Ensure checkpoint directory is persistent

### Scaling Strategy

1. **Horizontal Scaling**: Multiple instances with shared Redis cache
2. **Vertical Scaling**: Increase batch sizes and memory limits
3. **Load Balancing**: Distribute requests across instances
4. **Monitoring**: Track performance metrics and adjust accordingly

## Troubleshooting

### Common Issues

1. **Redis Connection**: Check Redis URL and connectivity
2. **OpenTelemetry**: Verify OTLP endpoint configuration
3. **Checkpoints**: Ensure checkpoint directory permissions
4. **Memory Usage**: Monitor cache memory consumption

### Debug Commands

```bash
# Check system health
make system-health

# Monitor cache performance
make cache-stats

# Verify tracing setup
make tracing-status

# Check batch processing
make batch-status
```

## Future Enhancements

### Planned Features

1. **Advanced Caching**: Cache warming and predictive loading
2. **Distributed Processing**: Multi-node batch processing
3. **Advanced Tracing**: Custom metrics and alerting
4. **Performance Tuning**: Automated optimization recommendations

### Integration Opportunities

1. **Prometheus**: Metrics collection and alerting
2. **Grafana**: Visualization and dashboards
3. **Jaeger**: Distributed tracing visualization
4. **Kubernetes**: Container orchestration and scaling
