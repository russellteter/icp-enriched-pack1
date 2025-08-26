"""
Historical Data Analyzer for ICP Discovery Engine
Analyzes historical run data from the runs/ directory to provide deep insights
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import pandas as pd
import numpy as np
import csv


@dataclass
class HistoricalRunData:
    """Structured historical run data"""
    run_id: str
    timestamp: datetime
    segment: str
    target_count: int
    mode: str
    region: str
    actual_results: int
    success_rate: float
    file_paths: Dict[str, str]
    run_duration: Optional[float]
    metadata: Dict[str, Any]


@dataclass
class SegmentTrend:
    """Trend analysis for a specific segment"""
    segment: str
    time_period: str
    total_runs: int
    avg_success_rate: float
    avg_results_per_run: float
    trend_direction: str  # improving, stable, declining
    peak_performance_date: str
    worst_performance_date: str
    consistency_score: float  # 0-1, how consistent the performance is
    seasonal_patterns: Dict[str, float]


@dataclass
class ComparisonAnalysis:
    """Comparison analysis between segments or time periods"""
    comparison_type: str  # segment_comparison, time_comparison
    comparison_subjects: List[str]
    metrics: Dict[str, Dict[str, float]]
    winner: str
    confidence_level: float
    insights: List[str]


class HistoricalAnalyzer:
    """Analyze historical run data for trends and insights"""
    
    def __init__(self, runs_dir: str = "runs"):
        self.runs_dir = Path(runs_dir)
        self.cache_file = Path("metrics/historical_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        
    def scan_historical_runs(self, refresh_cache: bool = False) -> List[HistoricalRunData]:
        """Scan runs directory for historical data"""
        if not refresh_cache and self.cache_file.exists():
            # Try to load from cache first
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    return [self._dict_to_historical_run(run_dict) for run_dict in cached_data]
            except:
                pass  # Fall back to scanning
        
        runs_data = []
        
        if not self.runs_dir.exists():
            return runs_data
        
        # Scan for run directories
        for run_dir in self.runs_dir.iterdir():
            if run_dir.is_dir() and run_dir.name.startswith("run_"):
                run_data = self._extract_run_data(run_dir)
                if run_data:
                    runs_data.append(run_data)
        
        # Also scan the 'latest' directory
        latest_dir = self.runs_dir / "latest"
        if latest_dir.exists():
            run_data = self._extract_run_data(latest_dir, is_latest=True)
            if run_data:
                runs_data.append(run_data)
        
        # Sort by timestamp
        runs_data.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Cache the results
        try:
            cache_data = [asdict(run) for run in runs_data]
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
        except:
            pass  # Don't fail if caching fails
        
        return runs_data
    
    def _extract_run_data(self, run_dir: Path, is_latest: bool = False) -> Optional[HistoricalRunData]:
        """Extract data from a single run directory"""
        try:
            # Parse run ID and timestamp from directory name
            if is_latest:
                run_id = "latest"
                timestamp = datetime.now()
            else:
                # Format: run_TIMESTAMP_HASH
                match = re.match(r'run_(\d+)_([a-f0-9]+)', run_dir.name)
                if not match:
                    return None
                
                timestamp_str, hash_str = match.groups()
                run_id = f"{timestamp_str}_{hash_str}"
                timestamp = datetime.fromtimestamp(int(timestamp_str))
            
            # Look for CSV files
            csv_files = list(run_dir.glob("*.csv"))
            if not csv_files:
                return None
            
            # Determine segment, target count, and results from files
            segment = self._determine_segment_from_files(csv_files)
            if not segment:
                return None
            
            # Count actual results from CSV
            actual_results = self._count_results_from_csv(run_dir / f"{segment}.csv")
            
            # Look for metadata or summary files
            metadata = self._extract_metadata(run_dir)
            
            # Estimate target count and other parameters
            target_count = metadata.get("target_count", 50)  # Default
            mode = metadata.get("mode", "fast")  # Default
            region = metadata.get("region", "both")  # Default
            run_duration = metadata.get("duration")
            
            # Calculate success rate (simplified)
            success_rate = min(1.0, actual_results / max(1, target_count))
            
            # Build file paths
            file_paths = {
                file.stem: str(file) for file in csv_files
            }
            
            return HistoricalRunData(
                run_id=run_id,
                timestamp=timestamp,
                segment=segment,
                target_count=target_count,
                mode=mode,
                region=region,
                actual_results=actual_results,
                success_rate=success_rate,
                file_paths=file_paths,
                run_duration=run_duration,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error processing run directory {run_dir}: {e}")
            return None
    
    def _determine_segment_from_files(self, csv_files: List[Path]) -> Optional[str]:
        """Determine segment from available CSV files"""
        for file in csv_files:
            filename = file.stem
            if filename in ["healthcare", "corporate", "providers"]:
                return filename
        return None
    
    def _count_results_from_csv(self, csv_file: Path) -> int:
        """Count results from CSV file"""
        if not csv_file.exists():
            return 0
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                # Skip header
                next(reader, None)
                return sum(1 for _ in reader)
        except:
            return 0
    
    def _extract_metadata(self, run_dir: Path) -> Dict[str, Any]:
        """Extract metadata from run directory"""
        metadata = {}
        
        # Look for summary.txt
        summary_file = run_dir / "summary.txt"
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    content = f.read()
                    # Parse summary for metadata
                    if "Target Count:" in content:
                        target_match = re.search(r'Target Count:\s*(\d+)', content)
                        if target_match:
                            metadata["target_count"] = int(target_match.group(1))
                    
                    if "Mode:" in content:
                        mode_match = re.search(r'Mode:\s*(\w+)', content)
                        if mode_match:
                            metadata["mode"] = mode_match.group(1)
                    
                    if "Region:" in content:
                        region_match = re.search(r'Region:\s*(\w+)', content)
                        if region_match:
                            metadata["region"] = region_match.group(1)
                    
                    if "Duration:" in content:
                        duration_match = re.search(r'Duration:\s*([0-9.]+)', content)
                        if duration_match:
                            metadata["duration"] = float(duration_match.group(1))
            except:
                pass
        
        # Look for metadata.json
        metadata_file = run_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    file_metadata = json.load(f)
                    metadata.update(file_metadata)
            except:
                pass
        
        return metadata
    
    def _dict_to_historical_run(self, run_dict: Dict) -> HistoricalRunData:
        """Convert dictionary back to HistoricalRunData"""
        run_dict = run_dict.copy()
        run_dict["timestamp"] = datetime.fromisoformat(run_dict["timestamp"])
        return HistoricalRunData(**run_dict)
    
    def analyze_segment_trends(self, days: int = 30) -> List[SegmentTrend]:
        """Analyze trends for each segment"""
        runs = self.scan_historical_runs()
        
        # Filter by time period
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_runs = [run for run in runs if run.timestamp > cutoff_date]
        
        # Group by segment
        segment_runs = defaultdict(list)
        for run in recent_runs:
            segment_runs[run.segment].append(run)
        
        trends = []
        for segment, runs_list in segment_runs.items():
            if len(runs_list) >= 3:  # Need at least 3 runs for trend analysis
                trend = self._calculate_segment_trend(segment, runs_list, days)
                trends.append(trend)
        
        return trends
    
    def _calculate_segment_trend(self, segment: str, runs: List[HistoricalRunData], days: int) -> SegmentTrend:
        """Calculate trend for a specific segment"""
        # Sort by timestamp
        runs = sorted(runs, key=lambda x: x.timestamp)
        
        # Calculate metrics
        total_runs = len(runs)
        avg_success_rate = sum(run.success_rate for run in runs) / total_runs
        avg_results_per_run = sum(run.actual_results for run in runs) / total_runs
        
        # Calculate trend direction using linear regression on success rates
        x = np.arange(len(runs))
        y = [run.success_rate for run in runs]
        
        if len(y) > 1:
            slope = np.polyfit(x, y, 1)[0]
            if slope > 0.05:  # 5% improvement trend
                trend_direction = "improving"
            elif slope < -0.05:  # 5% decline trend
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
        
        # Find peak and worst performance
        best_run = max(runs, key=lambda x: x.success_rate)
        worst_run = min(runs, key=lambda x: x.success_rate)
        
        peak_performance_date = best_run.timestamp.strftime('%Y-%m-%d')
        worst_performance_date = worst_run.timestamp.strftime('%Y-%m-%d')
        
        # Calculate consistency score (inverse of coefficient of variation)
        if avg_success_rate > 0:
            std_success_rate = np.std([run.success_rate for run in runs])
            cv = std_success_rate / avg_success_rate
            consistency_score = max(0, 1 - cv)  # Lower CV = higher consistency
        else:
            consistency_score = 0
        
        # Analyze seasonal patterns (day of week)
        day_performance = defaultdict(list)
        for run in runs:
            day_name = run.timestamp.strftime('%A')
            day_performance[day_name].append(run.success_rate)
        
        seasonal_patterns = {}
        for day, rates in day_performance.items():
            seasonal_patterns[day] = sum(rates) / len(rates) if rates else 0
        
        return SegmentTrend(
            segment=segment,
            time_period=f"{days}_days",
            total_runs=total_runs,
            avg_success_rate=avg_success_rate,
            avg_results_per_run=avg_results_per_run,
            trend_direction=trend_direction,
            peak_performance_date=peak_performance_date,
            worst_performance_date=worst_performance_date,
            consistency_score=consistency_score,
            seasonal_patterns=seasonal_patterns
        )
    
    def compare_segments(self, time_period: int = 30) -> ComparisonAnalysis:
        """Compare performance between segments"""
        trends = self.analyze_segment_trends(time_period)
        
        if len(trends) < 2:
            return ComparisonAnalysis(
                comparison_type="segment_comparison",
                comparison_subjects=[],
                metrics={},
                winner="insufficient_data",
                confidence_level=0.0,
                insights=["Insufficient data for segment comparison"]
            )
        
        # Compare key metrics
        metrics = {}
        for trend in trends:
            metrics[trend.segment] = {
                "avg_success_rate": trend.avg_success_rate,
                "avg_results_per_run": trend.avg_results_per_run,
                "consistency_score": trend.consistency_score,
                "total_runs": trend.total_runs
            }
        
        # Determine winner based on composite score
        segment_scores = {}
        for segment, metric_data in metrics.items():
            # Weighted score: 40% success rate, 30% consistency, 20% results, 10% run count
            score = (
                metric_data["avg_success_rate"] * 0.4 +
                metric_data["consistency_score"] * 0.3 +
                min(1.0, metric_data["avg_results_per_run"] / 50) * 0.2 +  # Normalize to target
                min(1.0, metric_data["total_runs"] / 10) * 0.1  # Reward more data
            )
            segment_scores[segment] = score
        
        winner = max(segment_scores, key=segment_scores.get)
        
        # Calculate confidence based on difference between top two
        sorted_scores = sorted(segment_scores.values(), reverse=True)
        if len(sorted_scores) > 1:
            confidence_level = min(1.0, (sorted_scores[0] - sorted_scores[1]) * 2)
        else:
            confidence_level = 1.0
        
        # Generate insights
        insights = []
        winner_metrics = metrics[winner]
        
        insights.append(f"{winner} segment performs best overall")
        insights.append(f"Best success rate: {winner_metrics['avg_success_rate']:.1%}")
        insights.append(f"Most consistent performer has {max(metrics.values(), key=lambda x: x['consistency_score'])}")
        
        # Compare trend directions
        improving_segments = [t.segment for t in trends if t.trend_direction == "improving"]
        if improving_segments:
            insights.append(f"Improving segments: {', '.join(improving_segments)}")
        
        declining_segments = [t.segment for t in trends if t.trend_direction == "declining"]
        if declining_segments:
            insights.append(f"Declining segments: {', '.join(declining_segments)} - need attention")
        
        return ComparisonAnalysis(
            comparison_type="segment_comparison",
            comparison_subjects=list(metrics.keys()),
            metrics=metrics,
            winner=winner,
            confidence_level=confidence_level,
            insights=insights
        )
    
    def analyze_time_periods(self, segment: str, periods: List[int] = [7, 14, 30]) -> List[Dict]:
        """Analyze performance across different time periods"""
        runs = self.scan_historical_runs()
        segment_runs = [run for run in runs if run.segment == segment]
        
        period_analysis = []
        
        for days in periods:
            cutoff_date = datetime.now() - timedelta(days=days)
            period_runs = [run for run in segment_runs if run.timestamp > cutoff_date]
            
            if period_runs:
                avg_success_rate = sum(run.success_rate for run in period_runs) / len(period_runs)
                avg_results = sum(run.actual_results for run in period_runs) / len(period_runs)
                total_runs = len(period_runs)
                
                # Calculate velocity (runs per day)
                velocity = total_runs / days
                
                period_analysis.append({
                    "period_days": days,
                    "total_runs": total_runs,
                    "avg_success_rate": avg_success_rate,
                    "avg_results_per_run": avg_results,
                    "velocity_runs_per_day": velocity,
                    "period_label": f"Last {days} days"
                })
        
        return period_analysis
    
    def get_performance_anomalies(self, segment: Optional[str] = None, threshold: float = 2.0) -> List[Dict]:
        """Identify performance anomalies using statistical analysis"""
        runs = self.scan_historical_runs()
        
        if segment:
            runs = [run for run in runs if run.segment == segment]
        
        if len(runs) < 10:  # Need sufficient data for anomaly detection
            return []
        
        # Calculate z-scores for success rates
        success_rates = [run.success_rate for run in runs]
        mean_rate = np.mean(success_rates)
        std_rate = np.std(success_rates)
        
        anomalies = []
        
        for run in runs:
            if std_rate > 0:
                z_score = abs(run.success_rate - mean_rate) / std_rate
                if z_score > threshold:
                    anomaly_type = "high_performance" if run.success_rate > mean_rate else "low_performance"
                    
                    anomalies.append({
                        "run_id": run.run_id,
                        "timestamp": run.timestamp.isoformat(),
                        "segment": run.segment,
                        "success_rate": run.success_rate,
                        "z_score": z_score,
                        "anomaly_type": anomaly_type,
                        "deviation_from_mean": run.success_rate - mean_rate
                    })
        
        # Sort by z-score (most anomalous first)
        anomalies.sort(key=lambda x: x["z_score"], reverse=True)
        
        return anomalies
    
    def generate_historical_insights(self) -> Dict[str, Any]:
        """Generate comprehensive insights from historical analysis"""
        runs = self.scan_historical_runs()
        
        if not runs:
            return {
                "error": "No historical data available",
                "insights": [],
                "recommendations": []
            }
        
        # Basic statistics
        total_runs = len(runs)
        date_range = (min(runs, key=lambda x: x.timestamp).timestamp, 
                     max(runs, key=lambda x: x.timestamp).timestamp)
        
        # Segment analysis
        segment_trends = self.analyze_segment_trends(30)
        segment_comparison = self.compare_segments(30)
        
        # Anomaly detection
        anomalies = self.get_performance_anomalies()
        
        # Generate insights
        insights = []
        recommendations = []
        
        insights.append(f"Analyzed {total_runs} historical runs")
        insights.append(f"Data spans from {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}")
        
        if segment_trends:
            best_trend = max(segment_trends, key=lambda x: x.avg_success_rate)
            insights.append(f"Best performing segment: {best_trend.segment} ({best_trend.avg_success_rate:.1%} success rate)")
            
            improving_segments = [t for t in segment_trends if t.trend_direction == "improving"]
            if improving_segments:
                insights.append(f"Improving segments: {', '.join([t.segment for t in improving_segments])}")
            
            declining_segments = [t for t in segment_trends if t.trend_direction == "declining"]
            if declining_segments:
                insights.append(f"Declining segments: {', '.join([t.segment for t in declining_segments])}")
                recommendations.append("Review extraction logic for declining segments")
        
        if len(anomalies) > 5:
            recommendations.append(f"High number of anomalies detected ({len(anomalies)}) - investigate data quality")
        
        # Usage patterns
        segment_counts = Counter(run.segment for run in runs)
        most_used_segment = segment_counts.most_common(1)[0][0]
        insights.append(f"Most frequently used segment: {most_used_segment}")
        
        # Mode analysis
        mode_counts = Counter(run.mode for run in runs if hasattr(run, 'mode'))
        if mode_counts:
            preferred_mode = mode_counts.most_common(1)[0][0]
            insights.append(f"Most frequently used mode: {preferred_mode}")
        
        return {
            "generated_at": datetime.now().isoformat(),
            "data_summary": {
                "total_runs": total_runs,
                "date_range": {
                    "start": date_range[0].isoformat(),
                    "end": date_range[1].isoformat()
                },
                "segments_analyzed": list(segment_counts.keys())
            },
            "segment_trends": [asdict(trend) for trend in segment_trends],
            "segment_comparison": asdict(segment_comparison),
            "anomalies_detected": len(anomalies),
            "top_anomalies": anomalies[:5],  # Top 5 anomalies
            "insights": insights,
            "recommendations": recommendations,
            "usage_patterns": {
                "segment_distribution": dict(segment_counts),
                "mode_distribution": dict(mode_counts) if mode_counts else {}
            }
        }
    
    def export_historical_analysis(self, format: str = "json") -> str:
        """Export historical analysis data"""
        insights = self.generate_historical_insights()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format.lower() == "json":
            output_file = Path(f"exports/historical_analysis_{timestamp}.json")
            output_file.parent.mkdir(exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(insights, f, indent=2, default=str)
            
            return str(output_file)
        
        elif format.lower() == "csv":
            # Export key data as CSV
            output_file = Path(f"exports/historical_analysis_{timestamp}.csv")
            output_file.parent.mkdir(exist_ok=True)
            
            # Flatten data for CSV
            csv_data = []
            
            for trend in insights.get("segment_trends", []):
                csv_data.append({
                    "type": "segment_trend",
                    "segment": trend["segment"],
                    "total_runs": trend["total_runs"],
                    "avg_success_rate": trend["avg_success_rate"],
                    "trend_direction": trend["trend_direction"],
                    "consistency_score": trend["consistency_score"]
                })
            
            for anomaly in insights.get("top_anomalies", []):
                csv_data.append({
                    "type": "anomaly",
                    "run_id": anomaly["run_id"],
                    "segment": anomaly["segment"],
                    "success_rate": anomaly["success_rate"],
                    "anomaly_type": anomaly["anomaly_type"],
                    "z_score": anomaly["z_score"]
                })
            
            if csv_data:
                df = pd.DataFrame(csv_data)
                df.to_csv(output_file, index=False)
            
            return str(output_file)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report for historical data"""
        runs = self.scan_historical_runs()
        
        if not runs:
            return {"error": "No data available"}
        
        # Analyze data completeness
        complete_runs = sum(1 for run in runs if run.actual_results > 0)
        completeness_rate = complete_runs / len(runs)
        
        # Check for data gaps
        runs_by_date = {}
        for run in runs:
            date_key = run.timestamp.strftime('%Y-%m-%d')
            runs_by_date[date_key] = runs_by_date.get(date_key, 0) + 1
        
        # Find gaps (days with no runs)
        if len(runs_by_date) > 1:
            start_date = min(datetime.strptime(d, '%Y-%m-%d') for d in runs_by_date.keys())
            end_date = max(datetime.strptime(d, '%Y-%m-%d') for d in runs_by_date.keys())
            
            total_days = (end_date - start_date).days + 1
            days_with_data = len(runs_by_date)
            coverage = days_with_data / total_days
        else:
            coverage = 1.0
        
        # Analyze consistency
        segments_consistency = {}
        for segment in ["healthcare", "corporate", "providers"]:
            segment_runs = [r for r in runs if r.segment == segment]
            if segment_runs:
                success_rates = [r.success_rate for r in segment_runs]
                consistency = 1 - (np.std(success_rates) / max(np.mean(success_rates), 0.1))
                segments_consistency[segment] = max(0, consistency)
        
        return {
            "total_runs_analyzed": len(runs),
            "completeness_rate": completeness_rate,
            "date_coverage": coverage,
            "segments_consistency": segments_consistency,
            "data_quality_score": (completeness_rate + coverage + np.mean(list(segments_consistency.values()))) / 3,
            "recommendations": self._generate_quality_recommendations(completeness_rate, coverage, segments_consistency)
        }
    
    def _generate_quality_recommendations(self, completeness: float, coverage: float, consistency: Dict[str, float]) -> List[str]:
        """Generate data quality recommendations"""
        recommendations = []
        
        if completeness < 0.8:
            recommendations.append("Low data completeness - investigate failed runs")
        
        if coverage < 0.7:
            recommendations.append("Irregular data collection - consider automated scheduling")
        
        for segment, consistency_score in consistency.items():
            if consistency_score < 0.6:
                recommendations.append(f"High variability in {segment} segment - review extraction logic")
        
        return recommendations