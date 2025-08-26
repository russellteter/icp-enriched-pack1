"""
Real-time monitoring dashboard for ICP Discovery Engine.
Provides system health, performance metrics, and resource usage tracking with brand styling.
"""

import streamlit as st
import time
from typing import Dict, Any, Optional, List
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from ..utils.api_client import get_api_client, display_api_error
from ..assets.brand_components import BrandComponents, ChartHelper


class MonitoringPanel:
    """Real-time system monitoring and performance dashboard."""
    
    def __init__(self):
        self.api_client = get_api_client()
        
    def render_system_overview(self):
        """Render high-level system status overview with brand styling."""
        BrandComponents.section_header(
            "🖥️ System Overview",
            "Real-time system health and component status monitoring"
        )
        
        # Get system health
        success, health_data = self.api_client.system_health()
        
        if success:
            # Status indicators with brand styling
            stats = {}
            
            status_color = "🟢" if health_data.status == "healthy" else "🔴"
            stats["System Status"] = f"{status_color} {health_data.status.title()}"
            
            uptime_hours = health_data.uptime / 3600
            stats["Uptime"] = f"{uptime_hours:.1f}h"
            
            current_time = datetime.fromtimestamp(health_data.timestamp)
            stats["Last Check"] = current_time.strftime("%H:%M:%S")
            
            # Component health summary
            healthy_components = sum(1 for comp in health_data.components.values() if isinstance(comp, dict))
            stats["Components"] = f"{healthy_components} Active"
            
            BrandComponents.quick_stats_grid(stats)
            
            return health_data
        else:
            st.markdown("""
            <div style="background: rgba(255, 77, 77, 0.1); border-left: 4px solid #ff4d4d; padding: 16px; border-radius: 6px; margin: 16px 0;">
                <p style="color: #ff4d4d; font-family: Inter; font-weight: 400; margin: 0;">
                    ❌ Unable to retrieve system health
                </p>
            </div>
            """, unsafe_allow_html=True)
            display_api_error(health_data, "System Health")
            return None
    
    def render_performance_metrics(self, health_data: Optional[Dict[str, Any]] = None):
        """Render performance metrics and resource usage."""
        st.subheader("📊 Performance Metrics")
        
        # Get detailed metrics
        success, metrics_data = self.api_client.get_metrics()
        
        if success:
            # Budget usage
            self._render_budget_usage(metrics_data.get("budget", {}))
            
            # Cache performance
            cache_success, cache_data = self.api_client.get_cache_stats()
            if cache_success:
                self._render_cache_performance(cache_data.get("cache", {}))
        else:
            st.error("❌ Unable to retrieve performance metrics")
            display_api_error(metrics_data, "Performance Metrics")
    
    def render_monitoring_dashboard(self):
        """Render comprehensive monitoring dashboard."""
        st.subheader("📈 Monitoring Dashboard")
        
        success, dashboard_data = self.api_client.get_monitoring_dashboard()
        
        if success:
            # Today's metrics
            today_data = dashboard_data.get("today", {})
            self._render_daily_metrics(today_data)
            
            # Trend analysis
            trends_data = dashboard_data.get("trends", {})
            self._render_trend_analysis(trends_data)
            
            # Alerts and issues
            alerts = dashboard_data.get("alerts", [])
            self._render_alerts(alerts)
            
        else:
            st.warning("Monitoring dashboard data unavailable - using basic metrics")
            self._render_basic_monitoring()
    
    def render_real_time_status(self):
        """Render real-time status indicators with auto-refresh."""
        st.subheader("⚡ Real-Time Status")
        
        # Auto-refresh controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            auto_refresh = st.checkbox("Auto-refresh", value=False)
            
        with col2:
            refresh_interval = st.selectbox("Interval", [5, 10, 30, 60], index=1)
        
        # Status container
        status_container = st.container()
        
        with status_container:
            # Component status checks
            self._render_component_status()
            
            # Resource utilization
            self._render_resource_utilization()
        
        # Auto-refresh logic
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()
    
    def _render_budget_usage(self, budget_config: Dict[str, Any]):
        """Render budget usage visualization."""
        if not budget_config:
            return
            
        st.write("**Resource Budget Configuration**")
        
        # Budget limits
        budget_metrics = {
            "Searches": budget_config.get("max_searches", 0),
            "Fetches": budget_config.get("max_fetches", 0), 
            "Enrichments": budget_config.get("max_enrich", 0),
            "LLM Tokens": budget_config.get("max_llm_tokens", 0)
        }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Max Searches", budget_metrics["Searches"])
        with col2:
            st.metric("Max Fetches", budget_metrics["Fetches"])
        with col3:
            st.metric("Max Enrichments", budget_metrics["Enrichments"])
        with col4:
            st.metric("Max LLM Tokens", f"{budget_metrics['LLM Tokens']:,}")
    
    def _render_cache_performance(self, cache_data: Dict[str, Any]):
        """Render cache performance metrics."""
        if not cache_data:
            return
            
        st.write("**Cache Performance**")
        
        stats = cache_data.get("stats", {})
        layers = cache_data.get("layers", 0)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cache Layers", layers)
        with col2:
            hit_rate = stats.get("hit_rate", 0)
            st.metric("Hit Rate", f"{hit_rate:.1%}")
        with col3:
            total_requests = stats.get("total_requests", 0)
            st.metric("Total Requests", f"{total_requests:,}")
        with col4:
            cache_size = stats.get("cache_size", 0)
            st.metric("Cache Size", f"{cache_size:,}")
    
    def _render_daily_metrics(self, today_data: Dict[str, Any]):
        """Render today's performance metrics."""
        if not today_data:
            return
            
        st.write("**Today's Activity**")
        
        discoveries = today_data.get("discoveries", {})
        quality = today_data.get("quality", {})
        costs = today_data.get("costs", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_discovered = sum(discoveries.values()) if discoveries else 0
            st.metric("Discoveries", total_discovered)
            
        with col2:
            acceptance_rate = quality.get("acceptance_rate", 0)
            st.metric("Quality Rate", f"{acceptance_rate:.1%}")
            
        with col3:
            daily_cost = costs.get("total_usd", 0)
            st.metric("Daily Cost", f"${daily_cost:.2f}")
            
        with col4:
            avg_time = quality.get("avg_execution_time", 0)
            st.metric("Avg Time", f"{avg_time:.1f}s")
    
    def _render_trend_analysis(self, trends_data: Dict[str, Any]):
        """Render trend analysis charts."""
        if not trends_data:
            return
            
        st.write("**7-Day Trends**")
        
        # Example trend visualization
        # In a real implementation, this would use actual historical data
        dates = [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)]
        discoveries = trends_data.get("daily_discoveries", [10, 15, 12, 18, 20, 16, 14])
        quality_rates = trends_data.get("quality_rates", [0.85, 0.88, 0.82, 0.90, 0.87, 0.89, 0.86])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                x=dates,
                y=discoveries,
                title="Daily Discoveries",
                labels={"x": "Date", "y": "Count"}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.line(
                x=dates,
                y=quality_rates,
                title="Quality Rate Trend",
                labels={"x": "Date", "y": "Rate"}
            )
            fig.update_layout(height=300, yaxis=dict(range=[0, 1]))
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_alerts(self, alerts: List[Dict[str, Any]]):
        """Render current alerts and issues."""
        st.write("**System Alerts**")
        
        if not alerts:
            st.success("✅ No active alerts")
            return
        
        for alert in alerts:
            severity = alert.get("severity", "info")
            message = alert.get("message", "Unknown alert")
            timestamp = alert.get("timestamp", time.time())
            
            if severity == "critical":
                st.error(f"🚨 {message} ({datetime.fromtimestamp(timestamp).strftime('%H:%M')})")
            elif severity == "warning":
                st.warning(f"⚠️ {message} ({datetime.fromtimestamp(timestamp).strftime('%H:%M')})")
            else:
                st.info(f"ℹ️ {message} ({datetime.fromtimestamp(timestamp).strftime('%H:%M')})")
    
    def _render_component_status(self):
        """Render individual component status checks."""
        st.write("**Component Status**")
        
        components = [
            ("Health Check", self.api_client.health_check),
            ("Cache Stats", self.api_client.get_cache_stats),
            ("Batch Status", self.api_client.get_batch_status),
            ("Tracing", self.api_client.get_tracing_status)
        ]
        
        col1, col2, col3, col4 = st.columns(4)
        columns = [col1, col2, col3, col4]
        
        for i, (name, check_func) in enumerate(components):
            with columns[i]:
                try:
                    success, _ = check_func()
                    status = "🟢 Healthy" if success else "🔴 Error"
                    st.metric(name, status)
                except:
                    st.metric(name, "🟡 Unknown")
    
    def _render_resource_utilization(self):
        """Render current resource utilization."""
        st.write("**Resource Utilization**")
        
        # Get system health for resource info
        success, health_data = self.api_client.system_health()
        
        if success and health_data.components:
            budget_info = health_data.components.get("budget", {})
            
            if budget_info:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    searches = budget_info.get("searches_used", 0)
                    st.metric("Searches Used", searches)
                    
                with col2:
                    fetches = budget_info.get("fetches_used", 0)
                    st.metric("Fetches Used", fetches)
                    
                with col3:
                    enrichments = budget_info.get("enrich_used", 0)
                    st.metric("Enrichments Used", enrichments)
                    
                with col4:
                    tokens = budget_info.get("llm_tokens_used", 0)
                    st.metric("LLM Tokens", f"{tokens:,}")
        else:
            st.info("Resource utilization data not available")
    
    def _render_basic_monitoring(self):
        """Render basic monitoring when advanced data is unavailable."""
        # Basic health check
        success, health = self.api_client.health_check()
        
        if success:
            st.success("✅ Basic health check passed")
        else:
            st.error("❌ Basic health check failed")
            
        # Basic metrics
        success, metrics = self.api_client.get_metrics()
        
        if success:
            st.info("📊 Basic metrics retrieved successfully")
        else:
            st.warning("⚠️ Unable to retrieve basic metrics")


def render_monitoring_panel():
    """Render the complete monitoring panel interface with brand styling."""
    monitor = MonitoringPanel()
    
    # System overview with brand styling
    health_data = monitor.render_system_overview()
    
    # Brand divider
    st.markdown("""
    <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
    """, unsafe_allow_html=True)
    
    # Performance metrics with brand styling
    monitor.render_performance_metrics(health_data)
    
    # Brand divider
    st.markdown("""
    <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
    """, unsafe_allow_html=True)
    
    # Monitoring dashboard with brand charts
    monitor.render_monitoring_dashboard()
    
    # Brand divider
    st.markdown("""
    <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
    """, unsafe_allow_html=True)
    
    # Real-time status with brand indicators
    monitor.render_real_time_status()