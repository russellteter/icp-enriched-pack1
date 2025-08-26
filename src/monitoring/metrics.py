"""
Observability and Monitoring for ICP Discovery Engine
Phase 3: Production-ready metrics, dashboards, and alerts
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import uuid


@dataclass
class RunMetrics:
    """Metrics for a single workflow run"""
    run_id: str
    segment: str
    start_time: float
    end_time: float
    duration: float
    
    # Budget metrics
    searches_used: int
    fetches_used: int
    enrichments_used: int
    llm_tokens_used: int
    
    # Quality metrics
    total_candidates: int
    confirmed_count: int
    probable_count: int
    excluded_count: int
    acceptance_rate: float  # confirmed / total
    
    # Regional mix
    na_count: int
    emea_count: int
    regional_mix_achieved: Dict[str, float]
    
    # Cache performance
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    
    # Error tracking
    errors: List[str]
    warnings: List[str]
    
    # Cost estimates (USD)
    estimated_search_cost: float
    estimated_enrichment_cost: float
    estimated_gpt_cost: float
    total_estimated_cost: float


class MetricsCollector:
    """Collect and store metrics for monitoring and alerting"""
    
    def __init__(self):
        self.metrics_dir = Path("metrics")
        self.metrics_dir.mkdir(exist_ok=True)
        self.daily_metrics_file = self.metrics_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Enhanced analytics tracking
        self.session_tracking_file = self.metrics_dir / "session_tracking.json"
        self.user_preferences_file = self.metrics_dir / "user_preferences.json"
        self.performance_history_file = self.metrics_dir / "performance_history.json"
        
    def record_run_metrics(self, metrics: RunMetrics):
        """Record metrics for a completed run"""
        metrics_data = asdict(metrics)
        metrics_data['timestamp'] = datetime.now().isoformat()
        
        # Append to daily metrics file
        daily_metrics = []
        if self.daily_metrics_file.exists():
            with open(self.daily_metrics_file, 'r') as f:
                daily_metrics = json.load(f)
        
        daily_metrics.append(metrics_data)
        
        with open(self.daily_metrics_file, 'w') as f:
            json.dump(daily_metrics, f, indent=2)
        
        # Also write latest metrics for dashboard
        latest_file = self.metrics_dir / "latest_run.json"
        with open(latest_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        # Track performance history for analytics
        self._update_performance_history(metrics)
        
        print(f"Recorded metrics for run {metrics.run_id}: {metrics.confirmed_count} confirmed, ${metrics.total_estimated_cost:.2f} cost")
    
    def _update_performance_history(self, metrics: RunMetrics):
        """Update performance history for trend analysis"""
        performance_entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": metrics.run_id,
            "segment": metrics.segment,
            "acceptance_rate": metrics.acceptance_rate,
            "cache_hit_rate": metrics.cache_hit_rate,
            "cost_per_discovery": metrics.total_estimated_cost / max(1, metrics.confirmed_count),
            "duration": metrics.duration,
            "budget_efficiency": {
                "searches_per_confirmed": metrics.searches_used / max(1, metrics.confirmed_count),
                "fetches_per_confirmed": metrics.fetches_used / max(1, metrics.confirmed_count),
                "enrichments_per_confirmed": metrics.enrichments_used / max(1, metrics.confirmed_count)
            }
        }
        
        # Load existing history
        history = []
        if self.performance_history_file.exists():
            try:
                with open(self.performance_history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append(performance_entry)
        
        # Keep only last 200 entries for performance
        if len(history) > 200:
            history = history[-200:]
        
        with open(self.performance_history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict:
        """Get summary metrics for a specific day"""
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        daily_file = self.metrics_dir / f"daily_{date}.json"
        if not daily_file.exists():
            return {"error": f"No metrics found for {date}"}
        
        with open(daily_file, 'r') as f:
            daily_runs = json.load(f)
        
        if not daily_runs:
            return {"date": date, "runs": 0}
        
        # Aggregate metrics
        total_runs = len(daily_runs)
        total_confirmed = sum(run["confirmed_count"] for run in daily_runs)
        total_probable = sum(run["probable_count"] for run in daily_runs)
        total_cost = sum(run["total_estimated_cost"] for run in daily_runs)
        avg_acceptance_rate = sum(run["acceptance_rate"] for run in daily_runs) / total_runs
        avg_cache_hit_rate = sum(run["cache_hit_rate"] for run in daily_runs) / total_runs if total_runs > 0 else 0
        
        # Budget utilization
        total_searches = sum(run["searches_used"] for run in daily_runs)
        total_fetches = sum(run["fetches_used"] for run in daily_runs)
        total_enrichments = sum(run["enrichments_used"] for run in daily_runs)
        total_tokens = sum(run["llm_tokens_used"] for run in daily_runs)
        
        # Regional mix across all runs
        total_na = sum(run["na_count"] for run in daily_runs)
        total_emea = sum(run["emea_count"] for run in daily_runs)
        total_regional = total_na + total_emea
        regional_mix = {
            "na": total_na / total_regional if total_regional > 0 else 0,
            "emea": total_emea / total_regional if total_regional > 0 else 0
        }
        
        # Error summary
        all_errors = []
        all_warnings = []
        for run in daily_runs:
            all_errors.extend(run.get("errors", []))
            all_warnings.extend(run.get("warnings", []))
        
        return {
            "date": date,
            "runs": total_runs,
            "discoveries": {
                "confirmed": total_confirmed,
                "probable": total_probable,
                "total": total_confirmed + total_probable
            },
            "quality": {
                "acceptance_rate": round(avg_acceptance_rate * 100, 1),
                "cache_hit_rate": round(avg_cache_hit_rate * 100, 1)
            },
            "budget_usage": {
                "searches": total_searches,
                "fetches": total_fetches,
                "enrichments": total_enrichments,
                "llm_tokens": total_tokens
            },
            "costs": {
                "total_usd": round(total_cost, 2),
                "avg_per_run": round(total_cost / total_runs, 2) if total_runs > 0 else 0
            },
            "regional_mix": regional_mix,
            "issues": {
                "errors": len(all_errors),
                "warnings": len(all_warnings),
                "top_errors": list(set(all_errors))[:5]
            }
        }
    
    def get_trend_analysis(self, days: int = 7) -> Dict:
        """Get trend analysis over the last N days"""
        trends = []
        base_date = datetime.now()
        
        for i in range(days):
            date = (base_date - timedelta(days=i)).strftime('%Y%m%d')
            daily_summary = self.get_daily_summary(date)
            if "error" not in daily_summary:
                trends.append(daily_summary)
        
        if not trends:
            return {"error": "No trend data available"}
        
        # Calculate trends
        recent_acceptance = sum(day["quality"]["acceptance_rate"] for day in trends[:3]) / min(3, len(trends))
        older_acceptance = sum(day["quality"]["acceptance_rate"] for day in trends[3:]) / max(1, len(trends) - 3)
        acceptance_trend = recent_acceptance - older_acceptance
        
        recent_cost = sum(day["costs"]["total_usd"] for day in trends[:3]) / min(3, len(trends))
        older_cost = sum(day["costs"]["total_usd"] for day in trends[3:]) / max(1, len(trends) - 3)
        cost_trend = recent_cost - older_cost
        
        return {
            "period_days": days,
            "total_runs": sum(day["runs"] for day in trends),
            "total_discoveries": sum(day["discoveries"]["total"] for day in trends),
            "trends": {
                "acceptance_rate": {
                    "current": round(recent_acceptance, 1),
                    "change": round(acceptance_trend, 1),
                    "direction": "improving" if acceptance_trend > 2 else "declining" if acceptance_trend < -2 else "stable"
                },
                "daily_cost": {
                    "current_avg": round(recent_cost, 2),
                    "change": round(cost_trend, 2),
                    "direction": "increasing" if cost_trend > 5 else "decreasing" if cost_trend < -5 else "stable"
                }
            },
            "daily_summaries": trends
        }
    
    def check_alerts(self) -> List[Dict]:
        """Check for conditions that should trigger alerts"""
        alerts = []
        
        # Get latest run metrics
        latest_file = self.metrics_dir / "latest_run.json"
        if not latest_file.exists():
            return alerts
        
        with open(latest_file, 'r') as f:
            latest_run = json.load(f)
        
        # Alert conditions per PRD
        
        # 1. Low acceptance rate
        if latest_run["acceptance_rate"] < 0.7:  # Below 70%
            alerts.append({
                "level": "warning",
                "type": "quality",
                "message": f"Low acceptance rate: {latest_run['acceptance_rate']*100:.1f}% (target: ≥70%)",
                "segment": latest_run["segment"],
                "run_id": latest_run["run_id"]
            })
        
        # 2. High cost per discovery
        cost_per_discovery = latest_run["total_estimated_cost"] / max(1, latest_run["confirmed_count"])
        if cost_per_discovery > 10:  # $10+ per confirmed discovery
            alerts.append({
                "level": "warning",
                "type": "cost",
                "message": f"High cost per discovery: ${cost_per_discovery:.2f} (threshold: $10)",
                "segment": latest_run["segment"],
                "run_id": latest_run["run_id"]
            })
        
        # 3. Poor regional mix (healthcare/corporate should target 80/20 NA/EMEA)
        if latest_run["segment"] in ["healthcare", "corporate"]:
            na_ratio = latest_run.get("regional_mix_achieved", {}).get("na", 0)
            if na_ratio < 0.6 or na_ratio > 0.9:  # Outside 60-90% range
                alerts.append({
                    "level": "warning",
                    "type": "regional_mix",
                    "message": f"Regional mix off-target: {na_ratio*100:.1f}% NA (target: 80%)",
                    "segment": latest_run["segment"],
                    "run_id": latest_run["run_id"]
                })
        
        # 4. Budget exhaustion
        if latest_run["llm_tokens_used"] > 3500:  # Near 4000 limit
            alerts.append({
                "level": "warning",
                "type": "budget",
                "message": f"LLM token budget near limit: {latest_run['llm_tokens_used']}/4000",
                "segment": latest_run["segment"],
                "run_id": latest_run["run_id"]
            })
        
        # 5. Frequent errors
        if len(latest_run.get("errors", [])) > 5:
            alerts.append({
                "level": "error",
                "type": "reliability",
                "message": f"Multiple errors in run: {len(latest_run['errors'])} errors",
                "segment": latest_run["segment"],
                "run_id": latest_run["run_id"]
            })
        
        return alerts
    
    def generate_dashboard_data(self) -> Dict:
        """Generate data for monitoring dashboard"""
        current_summary = self.get_daily_summary()
        trend_data = self.get_trend_analysis(7)
        alerts = self.check_alerts()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "status": "healthy" if not any(alert["level"] == "error" for alert in alerts) else "degraded",
            "today": current_summary,
            "trends": trend_data,
            "alerts": alerts,
            "system_health": {
                "cache_hit_rate": current_summary.get("quality", {}).get("cache_hit_rate", 0),
                "acceptance_rate": current_summary.get("quality", {}).get("acceptance_rate", 0),
                "daily_cost": current_summary.get("costs", {}).get("total_usd", 0)
            },
            "analytics_summary": self.get_analytics_summary()
        }
    
    def track_user_session(self, user_id: str, session_data: Dict):
        """Track user session for analytics"""
        session_entry = {
            "user_id": self._anonymize_user_id(user_id),
            "timestamp": datetime.now().isoformat(),
            "session_data": session_data,
            "session_id": str(uuid.uuid4())
        }
        
        # Load existing sessions
        sessions = []
        if self.session_tracking_file.exists():
            try:
                with open(self.session_tracking_file, 'r') as f:
                    sessions = json.load(f)
            except:
                sessions = []
        
        sessions.append(session_entry)
        
        # Keep only last 1000 sessions for performance
        if len(sessions) > 1000:
            sessions = sessions[-1000:]
        
        with open(self.session_tracking_file, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    def update_user_preferences(self, user_id: str, preferences: Dict):
        """Update user preferences for analytics"""
        anon_user_id = self._anonymize_user_id(user_id)
        
        # Load existing preferences
        user_prefs = {}
        if self.user_preferences_file.exists():
            try:
                with open(self.user_preferences_file, 'r') as f:
                    user_prefs = json.load(f)
            except:
                user_prefs = {}
        
        # Update preferences for this user
        if anon_user_id not in user_prefs:
            user_prefs[anon_user_id] = {
                "first_seen": datetime.now().isoformat(),
                "segment_counts": {},
                "mode_counts": {},
                "region_counts": {},
                "target_count_history": [],
                "last_updated": datetime.now().isoformat()
            }
        
        user_data = user_prefs[anon_user_id]
        user_data["last_updated"] = datetime.now().isoformat()
        
        # Update counts
        if "segment" in preferences:
            segment = preferences["segment"]
            user_data["segment_counts"][segment] = user_data["segment_counts"].get(segment, 0) + 1
        
        if "mode" in preferences:
            mode = preferences["mode"]
            user_data["mode_counts"][mode] = user_data["mode_counts"].get(mode, 0) + 1
        
        if "region" in preferences:
            region = preferences["region"]
            user_data["region_counts"][region] = user_data["region_counts"].get(region, 0) + 1
        
        if "target_count" in preferences:
            user_data["target_count_history"].append({
                "count": preferences["target_count"],
                "timestamp": datetime.now().isoformat()
            })
            # Keep only last 50 entries
            if len(user_data["target_count_history"]) > 50:
                user_data["target_count_history"] = user_data["target_count_history"][-50:]
        
        with open(self.user_preferences_file, 'w') as f:
            json.dump(user_prefs, f, indent=2)
    
    def _anonymize_user_id(self, user_id: str) -> str:
        """Create anonymized but consistent user ID"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def get_analytics_summary(self) -> Dict:
        """Get analytics summary for dashboard"""
        try:
            # User engagement metrics
            sessions = []
            if self.session_tracking_file.exists():
                with open(self.session_tracking_file, 'r') as f:
                    sessions = json.load(f)
            
            user_prefs = {}
            if self.user_preferences_file.exists():
                with open(self.user_preferences_file, 'r') as f:
                    user_prefs = json.load(f)
            
            # Calculate analytics
            total_users = len(user_prefs)
            total_sessions = len(sessions)
            
            # Session analysis for last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_sessions = [
                s for s in sessions 
                if datetime.fromisoformat(s["timestamp"]) > week_ago
            ]
            
            # Popular segments
            segment_popularity = defaultdict(int)
            for user_data in user_prefs.values():
                for segment, count in user_data.get("segment_counts", {}).items():
                    segment_popularity[segment] += count
            
            # Popular modes
            mode_popularity = defaultdict(int)
            for user_data in user_prefs.values():
                for mode, count in user_data.get("mode_counts", {}).items():
                    mode_popularity[mode] += count
            
            return {
                "user_engagement": {
                    "total_users": total_users,
                    "total_sessions": total_sessions,
                    "sessions_last_week": len(recent_sessions),
                    "avg_sessions_per_user": round(total_sessions / max(1, total_users), 1)
                },
                "usage_patterns": {
                    "popular_segments": dict(sorted(segment_popularity.items(), 
                                                   key=lambda x: x[1], reverse=True)[:3]),
                    "popular_modes": dict(sorted(mode_popularity.items(), 
                                                key=lambda x: x[1], reverse=True)[:3])
                },
                "activity_trend": self._calculate_activity_trend(sessions)
            }
        except Exception as e:
            return {
                "error": f"Analytics calculation failed: {str(e)}",
                "user_engagement": {"total_users": 0, "total_sessions": 0},
                "usage_patterns": {"popular_segments": {}, "popular_modes": {}},
                "activity_trend": "unknown"
            }
    
    def _calculate_activity_trend(self, sessions: List[Dict]) -> str:
        """Calculate user activity trend over time"""
        if len(sessions) < 14:
            return "insufficient_data"
        
        try:
            # Compare last 7 days to previous 7 days
            now = datetime.now()
            last_week = [s for s in sessions 
                        if (now - datetime.fromisoformat(s["timestamp"])).days <= 7]
            prev_week = [s for s in sessions 
                        if 7 < (now - datetime.fromisoformat(s["timestamp"])).days <= 14]
            
            if len(prev_week) == 0:
                return "stable"
            
            change_ratio = len(last_week) / len(prev_week)
            
            if change_ratio > 1.2:
                return "increasing"
            elif change_ratio < 0.8:
                return "decreasing"
            else:
                return "stable"
        except:
            return "unknown"
    
    def get_user_behavior_insights(self) -> Dict:
        """Get detailed user behavior insights"""
        try:
            user_prefs = {}
            if self.user_preferences_file.exists():
                with open(self.user_preferences_file, 'r') as f:
                    user_prefs = json.load(f)
            
            if not user_prefs:
                return {"insights": [], "recommendations": []}
            
            insights = []
            recommendations = []
            
            # Analyze segment preferences
            all_segment_counts = defaultdict(int)
            for user_data in user_prefs.values():
                for segment, count in user_data.get("segment_counts", {}).items():
                    all_segment_counts[segment] += count
            
            if all_segment_counts:
                most_popular = max(all_segment_counts, key=all_segment_counts.get)
                insights.append(f"Most popular segment: {most_popular} ({all_segment_counts[most_popular]} uses)")
            
            # Analyze user engagement
            active_users = sum(1 for user_data in user_prefs.values() 
                             if sum(user_data.get("segment_counts", {}).values()) > 5)
            
            engagement_rate = active_users / len(user_prefs) if user_prefs else 0
            
            if engagement_rate > 0.7:
                insights.append("High user engagement (70%+ are active users)")
            elif engagement_rate < 0.3:
                insights.append("Low user engagement (less than 30% are active)")
                recommendations.append("Consider improving user onboarding or adding tutorial")
            
            # Analyze mode preferences
            all_mode_counts = defaultdict(int)
            for user_data in user_prefs.values():
                for mode, count in user_data.get("mode_counts", {}).items():
                    all_mode_counts[mode] += count
            
            if all_mode_counts.get("deep", 0) > all_mode_counts.get("fast", 0) * 2:
                insights.append("Users prefer deep mode over fast mode")
                recommendations.append("Consider making deep mode the default")
            elif all_mode_counts.get("fast", 0) > all_mode_counts.get("deep", 0) * 3:
                insights.append("Users strongly prefer fast mode")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "user_stats": {
                    "total_users": len(user_prefs),
                    "active_users": active_users,
                    "engagement_rate": round(engagement_rate * 100, 1)
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to analyze user behavior: {str(e)}",
                "insights": [],
                "recommendations": []
            }
    
    def export_analytics_data(self) -> str:
        """Export analytics data for analysis"""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "daily_summaries": [],
                "user_preferences": {},
                "session_data": [],
                "performance_history": []
            }
            
            # Collect daily summaries for last 30 days
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                summary = self.get_daily_summary(date)
                if "error" not in summary:
                    export_data["daily_summaries"].append(summary)
            
            # Load user preferences
            if self.user_preferences_file.exists():
                with open(self.user_preferences_file, 'r') as f:
                    export_data["user_preferences"] = json.load(f)
            
            # Load session data
            if self.session_tracking_file.exists():
                with open(self.session_tracking_file, 'r') as f:
                    export_data["session_data"] = json.load(f)
            
            # Save export
            export_file = self.metrics_dir / f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return str(export_file)
            
        except Exception as e:
            return f"Export failed: {str(e)}"