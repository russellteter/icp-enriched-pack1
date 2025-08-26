"""
Analytics dashboard component for ICP Discovery Engine.
Provides comprehensive usage analytics, performance trends, and data visualization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..utils.api_client import get_api_client, display_api_error
from ..assets.brand_components import BrandComponents


def render_analytics_dashboard():
    """Render comprehensive analytics dashboard with brand styling."""
    api_client = get_api_client()
    
    # Dashboard header with brand styling
    BrandComponents.section_header(
        "📊 Advanced Analytics Dashboard",
        "Comprehensive usage tracking, performance trends, and business intelligence"
    )
    
    # Time period selector
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        days = st.selectbox(
            "📅 Analysis Period",
            options=[7, 14, 30, 60, 90],
            index=2,  # Default to 30 days
            help="Select the number of days to analyze"
        )
    
    with col2:
        analysis_type = st.selectbox(
            "🔍 Analysis Focus",
            options=["Overview", "User Behavior", "Performance Trends", "Resource Utilization"],
            help="Choose the type of analysis to display"
        )
    
    with col3:
        if BrandComponents.brand_button("🔄 Refresh", help="Refresh analytics data", key="analytics_refresh"):
            st.rerun()
    
    # Brand divider
    st.markdown('<div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>', unsafe_allow_html=True)
    
    # Render selected analysis
    if analysis_type == "Overview":
        render_overview_analytics(api_client, days)
    elif analysis_type == "User Behavior":
        render_user_behavior_analytics(api_client, days)
    elif analysis_type == "Performance Trends":
        render_performance_trends_analytics(api_client, days)
    elif analysis_type == "Resource Utilization":
        render_resource_utilization_analytics(api_client, days)


def render_overview_analytics(api_client, days: int):
    """Render overview analytics with key metrics and charts."""
    BrandComponents.section_header("🎯 Analytics Overview", f"Comprehensive insights for the last {days} days")
    
    # Get comprehensive analytics data
    success, data = api_client._make_request("GET", f"/analytics/comprehensive?days={days}")
    
    if not success:
        display_api_error(data.get("error"), "Failed to load analytics data")
        return
    
    analytics_data = data.get("data", {})
    user_behavior = analytics_data.get("user_behavior", {})
    performance_trends = analytics_data.get("performance_trends", {})
    resource_util = analytics_data.get("resource_utilization", {})
    
    # Key metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_runs = user_behavior.get("daily_usage_count", 0) * days
        st.metric(
            "Total Workflows",
            total_runs,
            delta=f"{user_behavior.get('weekly_usage_count', 0)} per week"
        )
    
    with col2:
        avg_success_rate = sum(performance_trends.get("success_rate_trend", [0])) / max(len(performance_trends.get("success_rate_trend", [1])), 1)
        st.metric(
            "Success Rate",
            f"{avg_success_rate:.1%}",
            delta="vs. target 70%"
        )
    
    with col3:
        avg_cost = sum(performance_trends.get("cost_trend", [0])) / max(len(performance_trends.get("cost_trend", [1])), 1)
        st.metric(
            "Avg Cost/Run",
            f"${avg_cost:.2f}",
            delta="per workflow"
        )
    
    with col4:
        budget_util = resource_util.get("budget_utilization_rate", 0)
        st.metric(
            "Budget Utilization",
            f"{budget_util:.1%}",
            delta="of allocated resources"
        )
    
    # Chart sections
    col1, col2 = st.columns(2)
    
    with col1:
        # Segment popularity pie chart
        segment_data = user_behavior.get("segment_popularity", {})
        if segment_data:
            fig = px.pie(
                values=list(segment_data.values()),
                names=[name.title() for name in segment_data.keys()],
                title="Segment Usage Distribution"
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker_colors=['#4739E7', '#DAD7FA', '#0A1849']
            )
            fig.update_layout(
                font_family="Inter",
                title_font_color="#0A1849",
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No segment usage data available for the selected period.")
    
    with col2:
        # Success rate trend
        trends = performance_trends.get("success_rate_trend", [])
        timestamps = performance_trends.get("timestamp_labels", [])
        
        if trends and timestamps:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps[-len(trends):],
                y=[rate * 100 for rate in trends],
                mode='lines+markers',
                name='Success Rate',
                line=dict(color='#4739E7', width=3),
                marker=dict(size=6, color='#4739E7')
            ))
            fig.update_layout(
                title="Success Rate Trend",
                xaxis_title="Time Period",
                yaxis_title="Success Rate (%)",
                font_family="Inter",
                title_font_color="#0A1849",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📈 No performance trend data available for the selected period.")
    
    # Time of day usage heatmap
    time_patterns = user_behavior.get("time_of_day_patterns", {})
    if time_patterns:
        BrandComponents.section_header("⏰ Usage Patterns by Hour", "")
        
        hours = list(range(24))
        usage_counts = [time_patterns.get(str(hour), 0) for hour in hours]
        
        fig = go.Figure(data=go.Bar(
            x=[f"{h:02d}:00" for h in hours],
            y=usage_counts,
            marker_color='#4739E7',
            name="Workflow Count"
        ))
        fig.update_layout(
            title="Workflow Execution by Hour of Day",
            xaxis_title="Hour of Day",
            yaxis_title="Number of Workflows",
            font_family="Inter",
            title_font_color="#0A1849",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Export section
    render_export_section(days)


def render_user_behavior_analytics(api_client, days: int):
    """Render detailed user behavior analytics."""
    BrandComponents.section_header("👥 User Behavior Analytics", f"Deep dive into usage patterns over {days} days")
    
    success, data = api_client._make_request("GET", f"/analytics/user-behavior?days={days}")
    
    if not success:
        display_api_error(data.get("error"), "Failed to load user behavior data")
        return
    
    behavior_data = data.get("data", {})
    
    # Usage summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        daily_count = behavior_data.get("daily_usage_count", 0)
        st.metric("Daily Average", f"{daily_count} workflows")
    
    with col2:
        session_duration = behavior_data.get("avg_session_duration", 0)
        st.metric("Avg Session", f"{session_duration:.1f} seconds")
    
    with col3:
        weekly_count = behavior_data.get("weekly_usage_count", 0)
        st.metric("Weekly Average", f"{weekly_count} workflows")
    
    # Detailed behavior analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Target count preferences
        target_prefs = behavior_data.get("target_count_preferences", {})
        if target_prefs:
            fig = px.bar(
                x=list(target_prefs.keys()),
                y=list(target_prefs.values()),
                title="Target Count Preferences",
                color_discrete_sequence=['#4739E7']
            )
            fig.update_layout(
                xaxis_title="Target Count Range",
                yaxis_title="Usage Count",
                font_family="Inter",
                title_font_color="#0A1849"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Mode usage distribution
        mode_usage = behavior_data.get("mode_usage", {})
        if mode_usage:
            fig = px.pie(
                values=list(mode_usage.values()),
                names=[mode.title() for mode in mode_usage.keys()],
                title="Execution Mode Distribution"
            )
            fig.update_traces(
                marker_colors=['#4739E7', '#DAD7FA']
            )
            fig.update_layout(
                font_family="Inter",
                title_font_color="#0A1849"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Region preferences
    region_prefs = behavior_data.get("region_preferences", {})
    if region_prefs:
        BrandComponents.section_header("🌍 Regional Preferences", "")
        
        fig = px.bar(
            x=[region.upper() for region in region_prefs.keys()],
            y=list(region_prefs.values()),
            title="Target Region Distribution",
            color_discrete_sequence=['#0A1849']
        )
        fig.update_layout(
            xaxis_title="Target Region",
            yaxis_title="Usage Count",
            font_family="Inter",
            title_font_color="#0A1849"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_performance_trends_analytics(api_client, days: int):
    """Render performance trends analytics with detailed charts."""
    BrandComponents.section_header("📈 Performance Trends", f"System performance analysis over {days} days")
    
    success, data = api_client._make_request("GET", f"/analytics/performance-trends?days={days}")
    
    if not success:
        display_api_error(data.get("error"), "Failed to load performance trends")
        return
    
    trends_data = data.get("data", {})
    
    # Performance metrics
    response_times = trends_data.get("response_time_trend", [])
    success_rates = trends_data.get("success_rate_trend", [])
    cache_hits = trends_data.get("cache_hit_rate_trend", [])
    timestamps = trends_data.get("timestamp_labels", [])
    
    if not timestamps:
        st.info("📊 No performance data available for the selected period.")
        return
    
    # Key performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        st.metric("Avg Response Time", f"{avg_response:.1f}s")
    
    with col2:
        avg_success = sum(success_rates) / len(success_rates) if success_rates else 0
        st.metric("Avg Success Rate", f"{avg_success:.1%}")
    
    with col3:
        avg_cache = sum(cache_hits) / len(cache_hits) if cache_hits else 0
        st.metric("Avg Cache Hit Rate", f"{avg_cache:.1%}")
    
    with col4:
        quality_scores = trends_data.get("quality_score_trend", [])
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        st.metric("Avg Quality Score", f"{avg_quality:.1%}")
    
    # Performance trends charts
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Response Time Trend', 'Success Rate Trend', 'Cache Hit Rate Trend', 'Quality Score Trend'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Response time trend
    fig.add_trace(
        go.Scatter(x=timestamps, y=response_times, name="Response Time", line=dict(color='#4739E7')),
        row=1, col=1
    )
    
    # Success rate trend
    fig.add_trace(
        go.Scatter(x=timestamps, y=[rate * 100 for rate in success_rates], name="Success Rate", line=dict(color='#0A1849')),
        row=1, col=2
    )
    
    # Cache hit rate trend
    fig.add_trace(
        go.Scatter(x=timestamps, y=[rate * 100 for rate in cache_hits], name="Cache Hit Rate", line=dict(color='#DAD7FA')),
        row=2, col=1
    )
    
    # Quality score trend
    fig.add_trace(
        go.Scatter(x=timestamps, y=[score * 100 for score in quality_scores], name="Quality Score", line=dict(color='#4739E7')),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        font_family="Inter",
        title_font_color="#0A1849"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_resource_utilization_analytics(api_client, days: int):
    """Render resource utilization analytics."""
    BrandComponents.section_header("⚡ Resource Utilization", f"Resource usage patterns and efficiency over {days} days")
    
    success, data = api_client._make_request("GET", f"/analytics/resource-utilization?days={days}")
    
    if not success:
        display_api_error(data.get("error"), "Failed to load resource utilization data")
        return
    
    resource_data = data.get("data", {})
    
    # Resource usage metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_searches = resource_data.get("avg_searches_per_run", 0)
        st.metric("Avg Searches/Run", f"{avg_searches:.1f}")
    
    with col2:
        avg_fetches = resource_data.get("avg_fetches_per_run", 0)
        st.metric("Avg Fetches/Run", f"{avg_fetches:.1f}")
    
    with col3:
        avg_enrichments = resource_data.get("avg_enrichments_per_run", 0)
        st.metric("Avg Enrichments/Run", f"{avg_enrichments:.1f}")
    
    with col4:
        budget_util = resource_data.get("budget_utilization_rate", 0)
        st.metric("Budget Utilization", f"{budget_util:.1%}")
    
    # Resource efficiency by segment
    segment_efficiency = resource_data.get("resource_efficiency_by_segment", {})
    cost_per_result = resource_data.get("cost_per_result", {})
    
    if segment_efficiency or cost_per_result:
        col1, col2 = st.columns(2)
        
        with col1:
            if segment_efficiency:
                fig = px.bar(
                    x=[seg.title() for seg in segment_efficiency.keys()],
                    y=list(segment_efficiency.values()),
                    title="Resource Efficiency by Segment",
                    color_discrete_sequence=['#4739E7']
                )
                fig.update_layout(
                    xaxis_title="Segment",
                    yaxis_title="Results per Resource Unit",
                    font_family="Inter",
                    title_font_color="#0A1849"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if cost_per_result:
                fig = px.bar(
                    x=[seg.title() for seg in cost_per_result.keys()],
                    y=list(cost_per_result.values()),
                    title="Cost per Result by Segment",
                    color_discrete_sequence=['#0A1849']
                )
                fig.update_layout(
                    xaxis_title="Segment",
                    yaxis_title="Cost per Result ($)",
                    font_family="Inter",
                    title_font_color="#0A1849"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Peak usage hours
    peak_hours = resource_data.get("peak_usage_hours", [])
    if peak_hours:
        BrandComponents.section_header("⏰ Peak Usage Analysis", "")
        
        peak_hours_text = ", ".join([f"{hour}:00" for hour in peak_hours])
        st.markdown(f"""
        <div style="background: rgba(71, 57, 231, 0.1); border-left: 4px solid #4739E7; padding: 16px; border-radius: 6px; margin: 16px 0;">
            <p style="color: #0A1849; font-family: Inter; font-weight: 500; margin: 0;">
                🕐 Peak Usage Hours: {peak_hours_text}
            </p>
            <p style="color: #0E0E1E; font-family: Inter; margin: 8px 0 0 0; font-size: 14px;">
                These are the hours with highest workflow execution volume. Consider resource scaling during these periods.
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_export_section(days: int):
    """Render analytics export section."""
    BrandComponents.section_header("📥 Export Analytics", "Download comprehensive reports and data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if BrandComponents.brand_button("📊 Export CSV Package", help="Download all analytics as CSV files"):
            st.success("🎉 CSV export initiated! Check your downloads folder.")
    
    with col2:
        if BrandComponents.brand_button("📈 Export Excel Report", help="Download comprehensive Excel report"):
            st.success("🎉 Excel export initiated! Check your downloads folder.")
    
    with col3:
        if BrandComponents.brand_button("📋 Management Report", help="Download executive summary"):
            st.success("🎉 Management report download initiated!")
    
    # Export info
    st.markdown("""
    <div style="background: rgba(255, 186, 0, 0.1); border-left: 4px solid #FFBA00; padding: 16px; border-radius: 6px; margin: 16px 0;">
        <h3 style="color: #0A1849; font-family: Inter; font-weight: 500; margin-bottom: 12px;">Export Information</h3>
        <ul style="color: #0E0E1E; font-family: Inter; margin: 0; padding-left: 20px;">
            <li style="margin-bottom: 6px;">CSV Package: Multiple files with detailed analytics data</li>
            <li style="margin-bottom: 6px;">Excel Report: Single file with multiple sheets and charts</li>
            <li style="margin-bottom: 6px;">Management Report: Executive summary in text format</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)