"""Batching and checkpointing functionality for scalable processing."""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass, asdict
from src.runtime.budget import BudgetManager


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 50
    checkpoint_interval: int = 10  # Checkpoint every N batches
    checkpoint_dir: str = "checkpoints"
    resume_from: Optional[str] = None  # Checkpoint file to resume from


@dataclass
class BatchState:
    """State for batch processing."""
    batch_id: str
    total_processed: int = 0
    total_batches: int = 0
    current_batch: int = 0
    last_checkpoint: Optional[str] = None
    budget_snapshot: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BatchProcessor:
    """Handles batching and checkpointing for large datasets."""
    
    def __init__(self, config: BatchConfig, budget: BudgetManager):
        self.config = config
        self.budget = budget
        self.checkpoint_dir = Path(config.checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # Resume from checkpoint if specified
        if config.resume_from:
            self.state = self._load_checkpoint(config.resume_from)
        else:
            self.state = BatchState(batch_id=f"batch_{int(time.time())}")
    
    def _load_checkpoint(self, checkpoint_file: str) -> BatchState:
        """Load state from checkpoint file."""
        checkpoint_path = self.checkpoint_dir / checkpoint_file
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")
        
        with checkpoint_path.open('r') as f:
            data = json.load(f)
        
        return BatchState(**data)
    
    def _save_checkpoint(self) -> str:
        """Save current state to checkpoint file."""
        timestamp = int(time.time())
        checkpoint_file = f"checkpoint_{self.state.batch_id}_{timestamp}.json"
        checkpoint_path = self.checkpoint_dir / checkpoint_file
        
        # Update state before saving
        self.state.last_checkpoint = checkpoint_file
        self.state.budget_snapshot = self.budget.snapshot()
        
        with checkpoint_path.open('w') as f:
            json.dump(asdict(self.state), f, indent=2)
        
        return checkpoint_file
    
    def process_batches(self, items: List[Dict[str, Any]], 
                       processor_func) -> Iterator[List[Dict[str, Any]]]:
        """Process items in batches with checkpointing."""
        total_items = len(items)
        total_batches = (total_items + self.config.batch_size - 1) // self.config.batch_size
        
        self.state.total_batches = total_batches
        
        for batch_num in range(self.state.current_batch, total_batches):
            start_idx = batch_num * self.config.batch_size
            end_idx = min(start_idx + self.config.batch_size, total_items)
            batch_items = items[start_idx:end_idx]
            
            self.state.current_batch = batch_num
            
            try:
                # Process the batch
                batch_results = processor_func(batch_items, self.budget)
                
                # Update state
                self.state.total_processed += len(batch_results)
                
                # Checkpoint if needed
                if batch_num % self.config.checkpoint_interval == 0:
                    checkpoint_file = self._save_checkpoint()
                    print(f"Checkpoint saved: {checkpoint_file}")
                
                yield batch_results
                
            except Exception as e:
                error_msg = f"Batch {batch_num} failed: {str(e)}"
                self.state.errors.append(error_msg)
                print(f"ERROR: {error_msg}")
                
                # Save checkpoint on error
                checkpoint_file = self._save_checkpoint()
                print(f"Error checkpoint saved: {checkpoint_file}")
                raise
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current processing progress."""
        return {
            "batch_id": self.state.batch_id,
            "current_batch": self.state.current_batch,
            "total_batches": self.state.total_batches,
            "total_processed": self.state.total_processed,
            "progress_percent": (self.state.current_batch / self.state.total_batches * 100) if self.state.total_batches > 0 else 0,
            "last_checkpoint": self.state.last_checkpoint,
            "errors": self.state.errors,
            "budget_snapshot": self.state.budget_snapshot
        }


def create_batch_processor(config: BatchConfig, budget: BudgetManager) -> BatchProcessor:
    """Factory function to create a batch processor."""
    return BatchProcessor(config, budget)
