"""
Structured Logging Module

Provides JSON-structured logging with budget tracking, performance metrics,
and observability features for the ICP Discovery Engine.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'batch_id'):
            log_entry['batch_id'] = record.batch_id
        if hasattr(record, 'segment'):
            log_entry['segment'] = record.segment
        if hasattr(record, 'region'):
            log_entry['region'] = record.region
        if hasattr(record, 'budget_counters'):
            log_entry['budget_counters'] = record.budget_counters
        if hasattr(record, 'url_allow_deny'):
            log_entry['url_allow_deny'] = record.url_allow_deny
        if hasattr(record, 'performance_metrics'):
            log_entry['performance_metrics'] = record.performance_metrics
        
        return json.dumps(log_entry)


class BudgetLogger:
    """Tracks and logs budget usage across workflow nodes."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.budget_snapshot = {}
    
    def log_budget_update(self, budget_counters: Dict[str, int], node: str):
        """Log budget counter updates."""
        extra = {
            'budget_counters': budget_counters,
            'node': node
        }
        self.logger.info(f"Budget update for {node}", extra=extra)
        self.budget_snapshot = budget_counters.copy()
    
    def log_budget_exceeded(self, budget_type: str, limit: int, current: int):
        """Log when a budget limit is exceeded."""
        extra = {
            'budget_counters': self.budget_snapshot,
            'budget_exceeded': {
                'type': budget_type,
                'limit': limit,
                'current': current
            }
        }
        self.logger.warning(f"Budget exceeded: {budget_type} ({current}/{limit})", extra=extra)


class URLLogger:
    """Tracks URL allow/deny decisions."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_url_decision(self, url: str, decision: str, reason: str, domain: str = None):
        """Log URL allow/deny decisions."""
        extra = {
            'url_allow_deny': {
                'url': url,
                'decision': decision,
                'reason': reason,
                'domain': domain
            }
        }
        self.logger.info(f"URL {decision}: {url} ({reason})", extra=extra)


class PerformanceLogger:
    """Tracks performance metrics and timing."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    @contextmanager
    def time_operation(self, operation: str, **kwargs):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            extra = {
                'performance_metrics': {
                    'operation': operation,
                    'duration_seconds': duration,
                    **kwargs
                }
            }
            self.logger.info(f"Operation completed: {operation} ({duration:.3f}s)", extra=extra)
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log custom performance metrics."""
        extra = {
            'performance_metrics': metrics
        }
        self.logger.info(f"Performance metrics: {metrics}", extra=extra)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    batch_id: Optional[str] = None,
    segment: Optional[str] = None,
    region: Optional[str] = None
) -> logging.Logger:
    """
    Set up structured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        batch_id: Batch identifier for correlation
        segment: ICP segment (healthcare, corporate, provider)
        region: Geographic region (na, emea, both)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with structured formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    # Add batch context to all log records
    if batch_id or segment or region:
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            if batch_id:
                record.batch_id = batch_id
            if segment:
                record.segment = segment
            if region:
                record.region = region
            return record
        
        logging.setLogRecordFactory(record_factory)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class WorkflowLogger:
    """High-level workflow logging interface."""
    
    def __init__(self, batch_id: str, segment: str, region: str):
        self.batch_id = batch_id
        self.segment = segment
        self.region = region
        
        # Set up logging with batch context
        self.logger = setup_logging(
            batch_id=batch_id,
            segment=segment,
            region=region
        )
        
        # Initialize specialized loggers
        self.budget_logger = BudgetLogger(self.logger)
        self.url_logger = URLLogger(self.logger)
        self.performance_logger = PerformanceLogger(self.logger)
    
    def log_workflow_start(self, target_count: int, mode: str):
        """Log workflow start."""
        extra = {
            'workflow': {
                'action': 'start',
                'target_count': target_count,
                'mode': mode
            }
        }
        self.logger.info(f"Workflow started: {self.segment} ({target_count} targets, {mode} mode)", extra=extra)
    
    def log_workflow_complete(self, outputs_count: int, budget_snapshot: Dict):
        """Log workflow completion."""
        extra = {
            'workflow': {
                'action': 'complete',
                'outputs_count': outputs_count,
                'budget_snapshot': budget_snapshot
            }
        }
        self.logger.info(f"Workflow completed: {outputs_count} outputs generated", extra=extra)
    
    def log_node_start(self, node: str, **kwargs):
        """Log node execution start."""
        extra = {
            'node': {
                'name': node,
                'action': 'start',
                **kwargs
            }
        }
        self.logger.info(f"Node started: {node}", extra=extra)
    
    def log_node_complete(self, node: str, **kwargs):
        """Log node execution completion."""
        extra = {
            'node': {
                'name': node,
                'action': 'complete',
                **kwargs
            }
        }
        self.logger.info(f"Node completed: {node}", extra=extra)
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context."""
        extra = {
            'error': {
                'type': type(error).__name__,
                'message': str(error),
                'context': context
            }
        }
        self.logger.error(f"Error in {context}: {error}", extra=extra)


# Global workflow logger instance
workflow_logger: Optional[WorkflowLogger] = None


def init_workflow_logger(batch_id: str, segment: str, region: str) -> WorkflowLogger:
    """Initialize global workflow logger."""
    global workflow_logger
    workflow_logger = WorkflowLogger(batch_id, segment, region)
    return workflow_logger


def get_workflow_logger() -> WorkflowLogger:
    """Get the global workflow logger instance."""
    if workflow_logger is None:
        raise RuntimeError("Workflow logger not initialized. Call init_workflow_logger first.")
    return workflow_logger
