"""
System Health Dashboard Component
Provides comprehensive system monitoring, performance metrics, and operational insights
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

from ..utils.api_client import get_api_client
from ..assets.brand_components import BrandComponents, ChartHelper


class SystemHealthDashboard:
    """Comprehensive system health monitoring dashboard."""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def render_complete_dashboard(self):
        """Render the complete system health dashboard."""
        # Main dashboard header
        BrandComponents.section_header(
            "🏥 System Health Dashboard",
            "Real-time monitoring, performance analytics, and operational insights"
        )
        
        # System overview
        self.render_system_overview()
        
        # Performance metrics
        self.render_performance_metrics()
        
        # Component health
        self.render_component_health()
        
        # Recent activity
        self.render_recent_activity()
        
        # Alerts and recommendations
        self.render_alerts_and_recommendations()
    
    def render_system_overview(self):
        """Render high-level system overview."""
        BrandComponents.section_header("📈 System Overview", "")
        
        # Get current metrics
        success, metrics = self.api_client.get_metrics()
        success_health, health_data = self.api_client.health_check()
        
        if success and success_health:
            # Create overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                uptime_hours = health_data.get('uptime_hours', 0)
                BrandComponents.brand_metric_card(
                    "System Uptime", 
                    f"{uptime_hours:.1f}h",
                    help="Hours since last restart"
                )
            
            with col2:
                cache_hit_rate = metrics.get('cache', {}).get('hit_rate', 0)
                BrandComponents.brand_metric_card(
                    "Cache Hit Rate",
                    f"{cache_hit_rate:.1%}",
                    help="Percentage of requests served from cache"
                )
            
            with col3:
                active_workflows = metrics.get('workflows', {}).get('active_count', 0)
                BrandComponents.brand_metric_card(
                    "Active Workflows",
                    str(active_workflows),
                    help="Currently executing workflows"
                )
            
            with col4:
                error_rate = metrics.get('errors', {}).get('rate_5min', 0)
                BrandComponents.brand_metric_card(
                    "Error Rate (5m)",
                    f"{error_rate:.2%}",
                    help="Error rate in the last 5 minutes"
                )
            
            # System status indicators
            self.render_status_indicators(health_data, metrics)
        else:
            st.error("❌ Unable to retrieve system metrics")
    
    def render_status_indicators(self, health_data: Dict, metrics: Dict):
        """Render system status indicators."""
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Overall system status
            overall_status = health_data.get('status', 'unknown')
            if overall_status == 'healthy':
                BrandComponents.status_indicator('success', 'System Healthy')
            else:
                BrandComponents.status_indicator('warning', f'Status: {overall_status}')
        
        with col2:
            # Database status
            db_status = health_data.get('database', {}).get('status', 'unknown')
            if db_status == 'connected':
                BrandComponents.status_indicator('online', 'Database Connected')
            else:
                BrandComponents.status_indicator('offline', f'Database: {db_status}')
        
        with col3:
            # Cache status
            cache_status = health_data.get('cache', {}).get('status', 'unknown')
            if cache_status == 'operational':
                BrandComponents.status_indicator('online', 'Cache Operational')
            else:
                BrandComponents.status_indicator('warning', f'Cache: {cache_status}')
    
    def render_performance_metrics(self):
        """Render performance metrics and charts."""
        BrandComponents.section_header("⚡ Performance Metrics", "")
        
        success, perf_data = self.api_client.get_performance_metrics()
        
        if success:
            # Response time metrics
            col1, col2 = st.columns(2)
            
            with col1:
                # Response time chart
                if 'response_times' in perf_data:
                    response_times = perf_data['response_times']
                    fig = ChartHelper.create_histogram(
                        response_times,
                        "API Response Time Distribution",
                        "Response Time (seconds)",
                        "Request Count"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Workflow completion rates
                if 'workflow_completion' in perf_data:
                    completion_data = perf_data['workflow_completion']
                    fig = ChartHelper.create_pie_chart(
                        completion_data,
                        "Workflow Completion Status"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Performance thresholds table
            self.render_performance_thresholds(perf_data)
        else:
            st.info("Performance metrics not available")
    
    def render_performance_thresholds(self, perf_data: Dict):
        """Render performance thresholds comparison table."""
        st.subheader("🎯 Performance Thresholds")
        
        thresholds_data = [
            {
                "Metric": "API Response Time (p95)",
                "Current": f"{perf_data.get('response_time_p95', 0):.2f}s",
                "Threshold": "< 2.0s",
                "Status": "✅ PASS" if perf_data.get('response_time_p95', 0) < 2.0 else "⚠️ SLOW"
            },
            {
                "Metric": "Workflow Success Rate",
                "Current": f"{perf_data.get('success_rate', 0):.1%}",
                "Threshold": "> 95%",
                "Status": "✅ PASS" if perf_data.get('success_rate', 0) > 0.95 else "⚠️ LOW"
            },
            {
                "Metric": "Cache Hit Rate",
                "Current": f"{perf_data.get('cache_hit_rate', 0):.1%}",
                "Threshold": "> 80%",
                "Status": "✅ PASS" if perf_data.get('cache_hit_rate', 0) > 0.8 else "⚠️ LOW"
            },
            {
                "Metric": "Memory Usage",
                "Current": f"{perf_data.get('memory_usage_pct', 0):.1f}%",
                "Threshold": "< 80%",
                "Status": "✅ PASS" if perf_data.get('memory_usage_pct', 0) < 80 else "⚠️ HIGH"
            }
        ]
        
        df = pd.DataFrame(thresholds_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def render_component_health(self):
        """Render individual component health status."""
        BrandComponents.section_header("🔧 Component Health", "")
        
        success, component_data = self.api_client.get_component_health()
        
        if success:
            components = ['API Server', 'Workflow Engine', 'Cache Layer', 'Database', 'External APIs']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Core Components")
                for component in components[:3]:
                    status = component_data.get(component.lower().replace(' ', '_'), {}).get('status', 'unknown')
                    last_check = component_data.get(component.lower().replace(' ', '_'), {}).get('last_check', 'N/A')
                    
                    if status == 'healthy':
                        st.markdown(f"✅ **{component}** - Healthy (checked: {last_check})")
                    elif status == 'degraded':
                        st.markdown(f"⚠️ **{component}** - Degraded (checked: {last_check})")
                    else:
                        st.markdown(f"❌ **{component}** - {status.title()} (checked: {last_check})")
            
            with col2:
                st.subheader("External Dependencies")
                for component in components[3:]:
                    status = component_data.get(component.lower().replace(' ', '_'), {}).get('status', 'unknown')
                    last_check = component_data.get(component.lower().replace(' ', '_'), {}).get('last_check', 'N/A')
                    
                    if status == 'healthy':
                        st.markdown(f"✅ **{component}** - Healthy (checked: {last_check})")
                    elif status == 'degraded':
                        st.markdown(f"⚠️ **{component}** - Degraded (checked: {last_check})")
                    else:
                        st.markdown(f"❌ **{component}** - {status.title()} (checked: {last_check})")
        else:
            st.info("Component health data not available")
    
    def render_recent_activity(self):
        """Render recent system activity and events."""
        BrandComponents.section_header("📊 Recent Activity", "")
        
        success, activity_data = self.api_client.get_recent_activity()
        
        if success:
            # Activity timeline
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Recent Workflows")
                workflows = activity_data.get('recent_workflows', [])
                if workflows:
                    for workflow in workflows[:5]:
                        timestamp = workflow.get('timestamp', 'Unknown')
                        segment = workflow.get('segment', 'unknown')
                        status = workflow.get('status', 'unknown')
                        count = workflow.get('result_count', 0)
                        
                        status_emoji = "✅" if status == "completed" else "❌"
                        st.markdown(f"{status_emoji} **{segment.title()}** - {count} results ({timestamp})")
                else:
                    st.info("No recent workflow activity")
            
            with col2:
                st.subheader("System Events")
                events = activity_data.get('system_events', [])
                if events:
                    for event in events[:5]:
                        timestamp = event.get('timestamp', 'Unknown')
                        event_type = event.get('type', 'info')
                        message = event.get('message', 'No message')
                        
                        emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(event_type, "ℹ️")
                        st.markdown(f"{emoji} {message} ({timestamp})")
                else:
                    st.info("No recent system events")
        else:
            st.info("Activity data not available")
    
    def render_alerts_and_recommendations(self):
        """Render system alerts and optimization recommendations."""
        BrandComponents.section_header("🚨 Alerts & Recommendations", "")
        
        success, alerts_data = self.api_client.get_system_alerts()
        
        if success:
            alerts = alerts_data.get('active_alerts', [])
            recommendations = alerts_data.get('recommendations', [])
            
            if alerts:
                st.subheader("🚨 Active Alerts")
                for alert in alerts:
                    severity = alert.get('severity', 'info')
                    message = alert.get('message', 'No message')
                    timestamp = alert.get('timestamp', 'Unknown')
                    
                    if severity == 'critical':
                        st.error(f"🔥 **CRITICAL**: {message} (since {timestamp})")
                    elif severity == 'warning':
                        st.warning(f"⚠️ **WARNING**: {message} (since {timestamp})")
                    else:
                        st.info(f"ℹ️ **INFO**: {message} (since {timestamp})")
            else:
                st.success("✅ No active alerts")
            
            if recommendations:
                st.subheader("💡 Optimization Recommendations")
                for rec in recommendations:
                    priority = rec.get('priority', 'low')
                    title = rec.get('title', 'Recommendation')
                    description = rec.get('description', 'No description')
                    impact = rec.get('impact', 'Unknown impact')
                    
                    priority_emoji = {"high": "🔥", "medium": "⚠️", "low": "💡"}.get(priority, "💡")
                    
                    with st.expander(f"{priority_emoji} {title} ({priority.upper()} priority)"):
                        st.markdown(f"**Description**: {description}")
                        st.markdown(f"**Expected Impact**: {impact}")
            else:
                st.info("No optimization recommendations at this time")
        else:
            st.info("Alerts and recommendations not available")
    
    def render_system_actions(self):
        """Render system maintenance actions."""
        st.subheader("🔧 System Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if BrandComponents.brand_button("🧹 Clear Cache", variant="secondary"):
                with st.spinner("Clearing cache..."):
                    success, result = self.api_client.clear_cache()
                    if success:
                        st.success("✅ Cache cleared successfully")
                    else:
                        st.error(f"❌ Failed to clear cache: {result}")
        
        with col2:
            if BrandComponents.brand_button("📊 Generate Report", variant="secondary"):
                with st.spinner("Generating system report..."):
                    success, report = self.api_client.generate_system_report()
                    if success:
                        st.success("✅ System report generated")
                        st.download_button(
                            label="📥 Download Report",
                            data=report,
                            file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error(f"❌ Failed to generate report: {report}")
        
        with col3:
            if BrandComponents.brand_button("🔄 Restart Services", variant="secondary"):
                if st.button("⚠️ Confirm Restart", help="This will restart background services"):
                    with st.spinner("Restarting services..."):
                        success, result = self.api_client.restart_services()
                        if success:
                            st.success("✅ Services restarted successfully")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to restart services: {result}")


def render_system_health_dashboard():
    """Render the complete system health dashboard."""
    dashboard = SystemHealthDashboard()
    dashboard.render_complete_dashboard()
    dashboard.render_system_actions()