"""
Advanced analytics engine for ICP Discovery Engine.
Tracks user behavior, performance trends, and resource utilization patterns.
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
import statistics

from .metrics import RunMetrics


@dataclass
class UserBehaviorMetrics:
    """User behavior tracking metrics."""
    segment_popularity: Dict[str, int]
    target_count_preferences: Dict[str, int]
    mode_usage: Dict[str, int]
    region_preferences: Dict[str, int]
    time_of_day_patterns: Dict[str, int]
    daily_usage_count: int
    weekly_usage_count: int
    avg_session_duration: float


@dataclass
class PerformanceTrends:
    """Performance trend metrics over time."""
    response_time_trend: List[float]
    success_rate_trend: List[float]
    cache_hit_rate_trend: List[float]
    quality_score_trend: List[float]
    resource_efficiency_trend: List[float]
    cost_trend: List[float]
    timestamp_labels: List[str]


@dataclass
class ResourceUtilization:
    """Resource utilization pattern analysis."""
    avg_searches_per_run: float
    avg_fetches_per_run: float
    avg_enrichments_per_run: float
    avg_tokens_per_run: float
    peak_usage_hours: List[int]
    resource_efficiency_by_segment: Dict[str, float]
    cost_per_result: Dict[str, float]
    budget_utilization_rate: float


class AdvancedAnalyticsEngine:
    """Advanced analytics engine for comprehensive usage tracking."""
    
    def __init__(self, runs_dir: Path = None):
        self.runs_dir = runs_dir or Path("runs")
        self.analytics_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def analyze_user_behavior(self, days: int = 30) -> UserBehaviorMetrics:
        """Analyze user behavior patterns over specified days."""
        cache_key = f"user_behavior_{days}"
        if self._is_cached(cache_key):
            return UserBehaviorMetrics(**self.analytics_cache[cache_key]["data"])
            
        # Get historical run data
        runs = self._get_recent_runs(days)
        
        # Initialize counters
        segment_counts = defaultdict(int)
        target_counts = defaultdict(int)
        mode_counts = defaultdict(int)
        region_counts = defaultdict(int)
        hour_counts = defaultdict(int)
        
        total_duration = 0
        session_count = 0
        
        for run_data in runs:
            # Extract patterns from run data
            if "segment" in run_data:
                segment_counts[run_data["segment"]] += 1
            if "targetcount" in run_data:
                count_range = self._categorize_target_count(run_data["targetcount"])
                target_counts[count_range] += 1
            if "mode" in run_data:
                mode_counts[run_data["mode"]] += 1
            if "region" in run_data:
                region_counts[run_data["region"]] += 1
            if "timestamp" in run_data:
                hour = datetime.fromtimestamp(run_data["timestamp"]).hour
                hour_counts[str(hour)] += 1
            if "duration" in run_data:
                total_duration += run_data["duration"]
                session_count += 1
        
        # Calculate averages and patterns
        avg_duration = total_duration / max(session_count, 1)
        
        behavior_metrics = UserBehaviorMetrics(
            segment_popularity=dict(segment_counts),
            target_count_preferences=dict(target_counts),
            mode_usage=dict(mode_counts),
            region_preferences=dict(region_counts),
            time_of_day_patterns=dict(hour_counts),
            daily_usage_count=len(runs) // max(days, 1),
            weekly_usage_count=len(runs) * 7 // max(days, 1),
            avg_session_duration=avg_duration
        )
        
        # Cache results
        self._cache_result(cache_key, asdict(behavior_metrics))
        return behavior_metrics
    
    def analyze_performance_trends(self, days: int = 30) -> PerformanceTrends:
        """Analyze performance trends over time."""
        cache_key = f"performance_trends_{days}"
        if self._is_cached(cache_key):
            return PerformanceTrends(**self.analytics_cache[cache_key]["data"])
            
        runs = self._get_recent_runs(days)
        
        # Sort by timestamp for trend analysis
        runs.sort(key=lambda x: x.get("timestamp", 0))
        
        response_times = []
        success_rates = []
        cache_hits = []
        quality_scores = []
        efficiency_scores = []
        costs = []
        timestamps = []
        
        for run_data in runs:
            # Response time trend
            if "duration" in run_data:
                response_times.append(run_data["duration"])
            else:
                response_times.append(120)  # Default estimate
                
            # Success rate (based on results vs target)
            results = run_data.get("confirmed_count", 0) + run_data.get("probable_count", 0)
            target = run_data.get("targetcount", 50)
            success_rate = min(results / max(target, 1), 1.0)
            success_rates.append(success_rate)
            
            # Cache hit rate
            cache_hit_rate = run_data.get("cache_hit_rate", 0.75)
            cache_hits.append(cache_hit_rate)
            
            # Quality score (acceptance rate)
            quality_score = run_data.get("acceptance_rate", 0.65)
            quality_scores.append(quality_score)
            
            # Resource efficiency (results per resource used)
            total_resources = (run_data.get("searches_used", 0) + 
                             run_data.get("fetches_used", 0) + 
                             run_data.get("enrichments_used", 0))
            efficiency = results / max(total_resources, 1)
            efficiency_scores.append(efficiency)
            
            # Cost trend
            cost = run_data.get("total_estimated_cost", 0)
            costs.append(cost)
            
            # Timestamp
            if "timestamp" in run_data:
                timestamps.append(datetime.fromtimestamp(run_data["timestamp"]).strftime("%m/%d"))
            else:
                timestamps.append("Unknown")
        
        trends = PerformanceTrends(
            response_time_trend=response_times[-20:],  # Last 20 runs
            success_rate_trend=success_rates[-20:],
            cache_hit_rate_trend=cache_hits[-20:],
            quality_score_trend=quality_scores[-20:],
            resource_efficiency_trend=efficiency_scores[-20:],
            cost_trend=costs[-20:],
            timestamp_labels=timestamps[-20:]
        )
        
        self._cache_result(cache_key, asdict(trends))
        return trends
    
    def analyze_resource_utilization(self, days: int = 30) -> ResourceUtilization:
        """Analyze resource utilization patterns."""
        cache_key = f"resource_util_{days}"
        if self._is_cached(cache_key):
            return ResourceUtilization(**self.analytics_cache[cache_key]["data"])
            
        runs = self._get_recent_runs(days)
        
        # Collect resource usage data
        searches = [r.get("searches_used", 0) for r in runs]
        fetches = [r.get("fetches_used", 0) for r in runs]
        enrichments = [r.get("enrichments_used", 0) for r in runs]
        tokens = [r.get("llm_tokens_used", 0) for r in runs]
        
        # Peak usage analysis by hour
        hour_counts = defaultdict(int)
        segment_efficiency = defaultdict(list)
        segment_costs = defaultdict(list)
        
        for run_data in runs:
            if "timestamp" in run_data:
                hour = datetime.fromtimestamp(run_data["timestamp"]).hour
                hour_counts[hour] += 1
            
            # Segment efficiency analysis
            segment = run_data.get("segment", "unknown")
            results = run_data.get("confirmed_count", 0) + run_data.get("probable_count", 0)
            total_resources = (run_data.get("searches_used", 0) + 
                             run_data.get("fetches_used", 0) + 
                             run_data.get("enrichments_used", 0))
            
            if total_resources > 0:
                efficiency = results / total_resources
                segment_efficiency[segment].append(efficiency)
            
            # Cost per result by segment
            cost = run_data.get("total_estimated_cost", 0)
            if results > 0:
                cost_per_result = cost / results
                segment_costs[segment].append(cost_per_result)
        
        # Calculate peak hours (top 3)
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_hours_list = [hour for hour, _ in peak_hours]
        
        # Calculate segment averages
        segment_eff_avg = {
            seg: statistics.mean(values) if values else 0
            for seg, values in segment_efficiency.items()
        }
        
        segment_cost_avg = {
            seg: statistics.mean(values) if values else 0
            for seg, values in segment_costs.items()
        }
        
        # Budget utilization (assuming max budgets)
        max_searches = 120
        max_fetches = 150
        max_enrichments = 80
        
        search_util = statistics.mean(searches) / max_searches if searches else 0
        fetch_util = statistics.mean(fetches) / max_fetches if fetches else 0
        enrich_util = statistics.mean(enrichments) / max_enrichments if enrichments else 0
        
        overall_util = (search_util + fetch_util + enrich_util) / 3
        
        utilization = ResourceUtilization(
            avg_searches_per_run=statistics.mean(searches) if searches else 0,
            avg_fetches_per_run=statistics.mean(fetches) if fetches else 0,
            avg_enrichments_per_run=statistics.mean(enrichments) if enrichments else 0,
            avg_tokens_per_run=statistics.mean(tokens) if tokens else 0,
            peak_usage_hours=peak_hours_list,
            resource_efficiency_by_segment=segment_eff_avg,
            cost_per_result=segment_cost_avg,
            budget_utilization_rate=overall_util
        )
        
        self._cache_result(cache_key, asdict(utilization))
        return utilization
    
    def get_comprehensive_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics combining all analysis types."""
        behavior = self.analyze_user_behavior(days)
        trends = self.analyze_performance_trends(days)
        resources = self.analyze_resource_utilization(days)
        
        return {
            "user_behavior": asdict(behavior),
            "performance_trends": asdict(trends),
            "resource_utilization": asdict(resources),
            "generated_at": datetime.now().isoformat(),
            "analysis_period_days": days
        }
    
    def _get_recent_runs(self, days: int) -> List[Dict[str, Any]]:
        """Get run data from the last N days."""
        cutoff_time = time.time() - (days * 24 * 3600)
        runs = []
        
        if not self.runs_dir.exists():
            return runs
        
        # Process run directories
        for run_dir in self.runs_dir.iterdir():
            if not run_dir.is_dir() or not run_dir.name.startswith("run_"):
                continue
                
            # Extract timestamp from directory name
            try:
                timestamp = int(run_dir.name.split("_")[1])
                if timestamp < cutoff_time:
                    continue
            except (IndexError, ValueError):
                continue
            
            # Read summary file for run data
            summary_file = run_dir / "summary.txt"
            if summary_file.exists():
                run_data = self._parse_summary_file(summary_file, timestamp)
                if run_data:
                    runs.append(run_data)
        
        return runs
    
    def _parse_summary_file(self, summary_file: Path, timestamp: int) -> Optional[Dict[str, Any]]:
        """Parse summary file to extract run data."""
        try:
            content = summary_file.read_text()
            run_data = {"timestamp": timestamp}
            
            # Parse key metrics from summary
            for line in content.split('\n'):
                if 'Segment=' in line:
                    run_data["segment"] = line.split('Segment=')[1].split(' ')[0].lower()
                elif 'total=' in line:
                    try:
                        run_data["confirmed_count"] = int(line.split('total=')[1].split(' ')[0])
                    except (IndexError, ValueError):
                        pass
                elif 'Target=' in line:
                    try:
                        run_data["targetcount"] = int(line.split('Target=')[1].split(' ')[0])
                    except (IndexError, ValueError):
                        pass
                elif 'Mode=' in line:
                    run_data["mode"] = line.split('Mode=')[1].split(' ')[0].lower()
                elif 'Region=' in line:
                    run_data["region"] = line.split('Region=')[1].split(' ')[0].lower()
            
            # Set defaults and estimates
            run_data.setdefault("probable_count", run_data.get("confirmed_count", 0) // 2)
            run_data.setdefault("searches_used", 45)
            run_data.setdefault("fetches_used", 60)
            run_data.setdefault("enrichments_used", 30)
            run_data.setdefault("llm_tokens_used", 15000)
            run_data.setdefault("duration", 120)
            run_data.setdefault("cache_hit_rate", 0.75)
            run_data.setdefault("total_estimated_cost", 2.50)
            
            # Calculate derived metrics
            results = run_data.get("confirmed_count", 0) + run_data.get("probable_count", 0)
            target = run_data.get("targetcount", 50)
            run_data["acceptance_rate"] = min(results / max(target, 1), 1.0)
            
            return run_data
            
        except Exception as e:
            print(f"Error parsing summary file {summary_file}: {e}")
            return None
    
    def _categorize_target_count(self, count: int) -> str:
        """Categorize target count into ranges."""
        if count <= 10:
            return "Small (1-10)"
        elif count <= 25:
            return "Medium (11-25)"
        elif count <= 50:
            return "Large (26-50)"
        else:
            return "Extra Large (51+)"
    
    def _is_cached(self, key: str) -> bool:
        """Check if result is cached and still valid."""
        if key not in self.analytics_cache:
            return False
        
        cached_time = self.analytics_cache[key]["timestamp"]
        return (time.time() - cached_time) < self.cache_ttl
    
    def _cache_result(self, key: str, data: Any):
        """Cache analysis result."""
        self.analytics_cache[key] = {
            "data": data,
            "timestamp": time.time()
        }