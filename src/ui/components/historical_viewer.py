"""
Historical run analysis and comparison component for ICP Discovery Engine.
Provides access to past runs, performance trends, and comparative analysis with brand styling.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from ..utils.api_client import get_api_client
from ..assets.brand_components import BrandComponents, ChartHelper


class HistoricalViewer:
    """Historical run analysis and comparison interface."""
    
    def __init__(self):
        self.runs_dir = Path("runs")
        self.api_client = get_api_client()
        
    def render_run_selector(self) -> Optional[Dict[str, Any]]:
        """Render run selection interface with filtering and brand styling."""
        BrandComponents.section_header(
            "📁 Historical Runs",
            "Browse and analyze past workflow executions and their results"
        )
        
        # Get available runs
        run_data = self._load_available_runs()
        
        if not run_data:
            st.markdown("""
            <div style="background: rgba(255, 186, 0, 0.1); border-left: 4px solid #FFBA00; padding: 16px; border-radius: 6px; margin: 16px 0;">
                <p style="color: #FFBA00; font-family: Inter; font-weight: 400; margin: 0;">
                    ⚠️ No historical runs found.
                </p>
            </div>
            """, unsafe_allow_html=True)
            return None
        
        # Create run selection interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Run selection dropdown
            run_options = {f"{run['display_name']}": run for run in run_data}
            selected_run_key = st.selectbox(
                "Select Run",
                options=list(run_options.keys()),
                help="Choose a historical run to analyze"
            )
            selected_run = run_options[selected_run_key]
            
        with col2:
            # Filter controls
            segment_filter = st.selectbox(
                "Filter by Segment",
                options=["All", "Healthcare", "Corporate", "Providers"]
            )
        
        # Apply filters
        if segment_filter != "All":
            filtered_runs = [run for run in run_data if run["segment"].lower() == segment_filter.lower()]
            if filtered_runs:
                run_options = {f"{run['display_name']}": run for run in filtered_runs}
                selected_run_key = st.selectbox(
                    "Filtered Runs",
                    options=list(run_options.keys()),
                    key="filtered_select"
                )
                selected_run = run_options[selected_run_key]
        
        return selected_run
    
    def render_run_details(self, run_info: Dict[str, Any]):
        """Render detailed information about a selected run."""
        st.subheader(f"📊 Run Details: {run_info['display_name']}")
        
        # Load run data
        run_data = self._load_run_data(run_info["path"])
        
        if not run_data:
            st.error("Unable to load run data.")
            return
        
        # Basic run information
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Segment", run_info["segment"].title())
        with col2:
            st.metric("Results Count", len(run_data["csv_data"]) if run_data["csv_data"] is not None else 0)
        with col3:
            st.metric("Run Date", run_info["date"].strftime("%m/%d/%Y"))
        with col4:
            st.metric("Run Time", run_info["time"].strftime("%H:%M"))
        
        # Run summary
        if run_data["summary"]:
            st.info(f"📝 **Summary:** {run_data['summary']}")
        
        # Results preview
        if run_data["csv_data"] is not None and not run_data["csv_data"].empty:
            st.subheader("📋 Results Preview")
            
            # Quality distribution
            self._render_historical_quality_distribution(run_data["csv_data"])
            
            # Data table
            st.dataframe(
                run_data["csv_data"].head(10),
                use_container_width=True,
                hide_index=True
            )
            
            if len(run_data["csv_data"]) > 10:
                with st.expander(f"View all {len(run_data['csv_data'])} results"):
                    st.dataframe(run_data["csv_data"], use_container_width=True, hide_index=True)
    
    def render_comparison_interface(self):
        """Render run comparison interface."""
        st.subheader("⚖️ Run Comparison")
        
        # Get available runs
        run_data = self._load_available_runs()
        
        if len(run_data) < 2:
            st.warning("Need at least 2 runs for comparison.")
            return
        
        # Run selection for comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**First Run**")
            run1_options = {f"{run['display_name']}": run for run in run_data}
            run1_key = st.selectbox("Select First Run", list(run1_options.keys()), key="compare_run1")
            run1 = run1_options[run1_key]
            
        with col2:
            st.write("**Second Run**") 
            # Filter out the first run from second selection
            run2_options = {f"{run['display_name']}": run for run in run_data if run["path"] != run1["path"]}
            run2_key = st.selectbox("Select Second Run", list(run2_options.keys()), key="compare_run2")
            run2 = run2_options[run2_key]
        
        # Load and compare runs
        if st.button("🔍 Compare Runs", type="primary"):
            self._render_run_comparison(run1, run2)
    
    def render_trend_analysis(self):
        """Render trend analysis across multiple runs."""
        st.subheader("📈 Performance Trends")
        
        # Get run data for trending
        run_data = self._load_available_runs()
        
        if len(run_data) < 3:
            st.warning("Need at least 3 runs for meaningful trend analysis.")
            return
        
        # Group by segment for analysis
        segments = list(set(run["segment"] for run in run_data))
        
        selected_segment = st.selectbox(
            "Analyze Trends for Segment",
            options=segments + ["All Segments"]
        )
        
        # Filter runs by segment if needed
        if selected_segment != "All Segments":
            filtered_runs = [run for run in run_data if run["segment"] == selected_segment]
        else:
            filtered_runs = run_data
        
        # Generate trend charts
        self._render_trend_charts(filtered_runs, selected_segment)
    
    def render_performance_analytics(self):
        """Render advanced performance analytics."""
        st.subheader("🎯 Performance Analytics")
        
        # Load recent runs for analytics
        recent_runs = self._load_recent_runs(limit=10)
        
        if not recent_runs:
            st.warning("No recent runs available for analytics.")
            return
        
        # Analytics tabs
        tab1, tab2, tab3 = st.tabs(["Quality Metrics", "Efficiency Analysis", "Success Patterns"])
        
        with tab1:
            self._render_quality_analytics(recent_runs)
            
        with tab2:
            self._render_efficiency_analytics(recent_runs)
            
        with tab3:
            self._render_success_patterns(recent_runs)
    
    def _load_available_runs(self) -> List[Dict[str, Any]]:
        """Load metadata for all available runs."""
        runs = []
        
        if not self.runs_dir.exists():
            return runs
        
        # Get all run directories
        for run_dir in self.runs_dir.iterdir():
            if run_dir.is_dir() and run_dir.name.startswith("run_"):
                run_info = self._parse_run_directory(run_dir)
                if run_info:
                    runs.append(run_info)
        
        # Sort by timestamp (newest first)
        runs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return runs
    
    def _parse_run_directory(self, run_dir: Path) -> Optional[Dict[str, Any]]:
        """Parse run directory to extract metadata."""
        try:
            # Parse run directory name: run_TIMESTAMP_HASH
            parts = run_dir.name.split("_")
            if len(parts) >= 2:
                timestamp = int(parts[1])
                run_id = parts[2] if len(parts) > 2 else "unknown"
            else:
                return None
            
            # Determine segment from available CSV files
            csv_files = list(run_dir.glob("*.csv"))
            if not csv_files:
                return None
                
            # Use the first CSV file to determine segment
            segment = csv_files[0].stem
            
            # Create display name
            dt = datetime.fromtimestamp(timestamp)
            display_name = f"{segment.title()} - {dt.strftime('%m/%d %H:%M')}"
            
            return {
                "path": run_dir,
                "timestamp": timestamp,
                "date": dt.date(),
                "time": dt.time(),
                "run_id": run_id,
                "segment": segment,
                "display_name": display_name,
                "csv_files": [f.name for f in csv_files]
            }
            
        except (ValueError, IndexError):
            return None
    
    def _load_run_data(self, run_path: Path) -> Dict[str, Any]:
        """Load complete data for a specific run."""
        data = {
            "csv_data": None,
            "summary": None
        }
        
        # Load CSV data
        csv_files = list(run_path.glob("*.csv"))
        if csv_files:
            try:
                data["csv_data"] = pd.read_csv(csv_files[0])
            except Exception as e:
                st.error(f"Error loading CSV: {e}")
        
        # Load summary
        summary_file = run_path / "summary.txt"
        if summary_file.exists():
            try:
                data["summary"] = summary_file.read_text().strip()
            except Exception as e:
                st.error(f"Error loading summary: {e}")
        
        return data
    
    def _load_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Load recent runs with their data for analytics."""
        all_runs = self._load_available_runs()
        recent_runs = []
        
        for run in all_runs[:limit]:
            run_data = self._load_run_data(run["path"])
            if run_data["csv_data"] is not None:
                run["data"] = run_data
                recent_runs.append(run)
        
        return recent_runs
    
    def _render_historical_quality_distribution(self, df: pd.DataFrame):
        """Render quality distribution for historical data."""
        if 'Tier' not in df.columns:
            return
            
        tier_counts = df['Tier'].value_counts()
        
        fig = px.pie(
            values=tier_counts.values,
            names=tier_counts.index,
            title="Quality Distribution",
            color_discrete_sequence=['#28a745', '#ffc107', '#fd7e14', '#dc3545']
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=300, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_run_comparison(self, run1: Dict[str, Any], run2: Dict[str, Any]):
        """Render detailed comparison between two runs."""
        st.subheader("📊 Comparison Results")
        
        # Load data for both runs
        data1 = self._load_run_data(run1["path"])
        data2 = self._load_run_data(run2["path"])
        
        if data1["csv_data"] is None or data2["csv_data"] is None:
            st.error("Unable to load data for comparison.")
            return
        
        # Basic comparison metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Results Count",
                len(data2["csv_data"]),
                delta=len(data2["csv_data"]) - len(data1["csv_data"])
            )
            
        with col2:
            if 'Score' in data1["csv_data"].columns and 'Score' in data2["csv_data"].columns:
                avg1 = data1["csv_data"]['Score'].mean()
                avg2 = data2["csv_data"]['Score'].mean()
                st.metric(
                    "Avg Score",
                    f"{avg2:.1f}",
                    delta=f"{avg2 - avg1:.1f}"
                )
                
        with col3:
            if 'Tier' in data1["csv_data"].columns and 'Tier' in data2["csv_data"].columns:
                quality1 = len(data1["csv_data"][data1["csv_data"]['Tier'].str.contains('Confirmed|Tier 1', na=False)])
                quality2 = len(data2["csv_data"][data2["csv_data"]['Tier'].str.contains('Confirmed|Tier 1', na=False)])
                st.metric(
                    "High Quality",
                    quality2,
                    delta=quality2 - quality1
                )
        
        # Side-by-side quality distribution
        if 'Tier' in data1["csv_data"].columns and 'Tier' in data2["csv_data"].columns:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**{run1['display_name']}**")
                tier_counts1 = data1["csv_data"]['Tier'].value_counts()
                fig1 = px.bar(x=tier_counts1.index, y=tier_counts1.values, title="Quality Distribution")
                fig1.update_layout(height=300)
                st.plotly_chart(fig1, use_container_width=True)
                
            with col2:
                st.write(f"**{run2['display_name']}**")
                tier_counts2 = data2["csv_data"]['Tier'].value_counts()
                fig2 = px.bar(x=tier_counts2.index, y=tier_counts2.values, title="Quality Distribution")
                fig2.update_layout(height=300)
                st.plotly_chart(fig2, use_container_width=True)
    
    def _render_trend_charts(self, runs: List[Dict[str, Any]], segment: str):
        """Render trend analysis charts."""
        if len(runs) < 3:
            return
        
        # Extract trend data
        dates = []
        result_counts = []
        avg_scores = []
        quality_rates = []
        
        for run in sorted(runs, key=lambda x: x["timestamp"]):
            data = self._load_run_data(run["path"])
            if data["csv_data"] is not None:
                dates.append(run["date"])
                result_counts.append(len(data["csv_data"]))
                
                if 'Score' in data["csv_data"].columns:
                    avg_scores.append(data["csv_data"]['Score'].mean())
                else:
                    avg_scores.append(0)
                    
                if 'Tier' in data["csv_data"].columns:
                    quality_count = len(data["csv_data"][data["csv_data"]['Tier'].str.contains('Confirmed|Tier 1', na=False)])
                    quality_rates.append(quality_count / len(data["csv_data"]))
                else:
                    quality_rates.append(0)
        
        if not dates:
            st.warning("No data available for trend analysis.")
            return
        
        # Create trend charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                x=dates,
                y=result_counts,
                title=f"Results Count Trend - {segment}",
                labels={"x": "Date", "y": "Count"}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.line(
                x=dates,
                y=quality_rates,
                title=f"Quality Rate Trend - {segment}",
                labels={"x": "Date", "y": "Quality Rate"}
            )
            fig.update_layout(height=300, yaxis=dict(range=[0, 1]))
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_quality_analytics(self, runs: List[Dict[str, Any]]):
        """Render quality analytics across runs."""
        st.write("**Quality Performance Analysis**")
        
        segment_quality = {}
        for run in runs:
            segment = run["segment"]
            if segment not in segment_quality:
                segment_quality[segment] = []
                
            df = run["data"]["csv_data"]
            if 'Tier' in df.columns:
                quality_count = len(df[df['Tier'].str.contains('Confirmed|Tier 1', na=False)])
                quality_rate = quality_count / len(df) if len(df) > 0 else 0
                segment_quality[segment].append(quality_rate)
        
        # Average quality by segment
        avg_quality = {seg: sum(rates) / len(rates) for seg, rates in segment_quality.items() if rates}
        
        if avg_quality:
            fig = px.bar(
                x=list(avg_quality.keys()),
                y=list(avg_quality.values()),
                title="Average Quality Rate by Segment"
            )
            fig.update_layout(height=300, yaxis=dict(range=[0, 1]))
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_efficiency_analytics(self, runs: List[Dict[str, Any]]):
        """Render efficiency analytics."""
        st.write("**Efficiency Analysis**")
        
        # Results per segment
        segment_results = {}
        for run in runs:
            segment = run["segment"]
            if segment not in segment_results:
                segment_results[segment] = []
            segment_results[segment].append(len(run["data"]["csv_data"]))
        
        # Average results by segment
        avg_results = {seg: sum(counts) / len(counts) for seg, counts in segment_results.items() if counts}
        
        if avg_results:
            fig = px.bar(
                x=list(avg_results.keys()),
                y=list(avg_results.values()),
                title="Average Results Count by Segment"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_success_patterns(self, runs: List[Dict[str, Any]]):
        """Render success pattern analysis."""
        st.write("**Success Patterns**")
        
        # Most common tiers across all runs
        all_tiers = []
        for run in runs:
            df = run["data"]["csv_data"]
            if 'Tier' in df.columns:
                all_tiers.extend(df['Tier'].tolist())
        
        if all_tiers:
            tier_counts = pd.Series(all_tiers).value_counts()
            
            fig = px.pie(
                values=tier_counts.values,
                names=tier_counts.index,
                title="Overall Tier Distribution (All Recent Runs)"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


def render_historical_viewer():
    """Render the complete historical viewer interface with brand styling."""
    viewer = HistoricalViewer()
    
    # Create tabs for different views with brand styling
    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Browse Runs", 
        "⚖️ Compare Runs", 
        "📈 Trends", 
        "🔬 Analytics"
    ])
    
    with tab1:
        selected_run = viewer.render_run_selector()
        if selected_run:
            # Brand divider
            st.markdown("""
            <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
            """, unsafe_allow_html=True)
            viewer.render_run_details(selected_run)
    
    with tab2:
        viewer.render_comparison_interface()
    
    with tab3:
        viewer.render_trend_analysis()
    
    with tab4:
        viewer.render_performance_analytics()