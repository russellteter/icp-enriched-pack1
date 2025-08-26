"""
Results visualization and analysis component for ICP Discovery Engine.
Provides advanced filtering, data analysis, and export capabilities with brand styling.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import base64

from ..utils.api_client import WorkflowResult
from ..assets.brand_components import BrandComponents, ChartHelper


class ResultsAnalyzer:
    """Advanced results analysis and visualization."""
    
    def __init__(self):
        self.tier_colors = {
            "Confirmed": "#28a745",    # Green
            "Probable": "#ffc107",     # Yellow  
            "Excluded": "#dc3545",     # Red
            "Tier 1": "#28a745",
            "Tier 2": "#ffc107", 
            "Tier 3": "#fd7e14"        # Orange
        }
        
    def render_results_overview(self, result: WorkflowResult):
        """Render high-level results overview with key metrics and brand styling."""
        # Section header with brand styling
        BrandComponents.section_header(
            f"📊 {result.segment.title()} Discovery Results",
            "Overview of discovered organizations with quality metrics and distribution analysis"
        )
        
        if not result.outputs:
            st.markdown("""
            <div style="background: rgba(255, 186, 0, 0.1); border-left: 4px solid #FFBA00; padding: 16px; border-radius: 6px; margin: 16px 0;">
                <p style="color: #FFBA00; font-family: Inter; font-weight: 400; margin: 0;">
                    ⚠️ No results to display.
                </p>
            </div>
            """, unsafe_allow_html=True)
            return
            
        # Convert to DataFrame for analysis
        df = self._convert_to_dataframe(result.outputs)
        
        # Key metrics with brand styling
        stats = {}
        stats["Total Found"] = len(df)
        
        confirmed = len(df[df['Tier'].str.contains('Confirmed|Tier 1', case=False, na=False)])
        stats["High Quality"] = confirmed
        
        avg_score = df['Score'].mean() if 'Score' in df.columns else 0
        stats["Avg Score"] = f"{avg_score:.1f}"
        
        na_count = len(df[df['Region'].str.contains('NA', case=False, na=False)])
        stats["North America"] = na_count
        
        BrandComponents.quick_stats_grid(stats)
        
        # Distribution charts with brand styling
        self._render_tier_distribution(df)
        self._render_regional_distribution(df)
        
        return df
    
    def render_interactive_table(self, df: pd.DataFrame):
        """Render interactive data table with filtering and sorting."""
        st.subheader("🔍 Interactive Results Table")
        
        # Filtering controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Tier filter
            tier_options = ["All"] + sorted(df['Tier'].unique().tolist()) if 'Tier' in df.columns else ["All"]
            selected_tier = st.selectbox("Filter by Tier", tier_options)
            
        with col2:
            # Region filter
            region_options = ["All"] + sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else ["All"]
            selected_region = st.selectbox("Filter by Region", region_options)
            
        with col3:
            # Score filter
            if 'Score' in df.columns:
                score_range = st.slider(
                    "Minimum Score",
                    min_value=int(df['Score'].min()),
                    max_value=int(df['Score'].max()),
                    value=int(df['Score'].min())
                )
            else:
                score_range = 0
        
        # Apply filters
        filtered_df = df.copy()
        
        if selected_tier != "All":
            filtered_df = filtered_df[filtered_df['Tier'] == selected_tier]
            
        if selected_region != "All":
            filtered_df = filtered_df[filtered_df['Region'] == selected_region]
            
        if 'Score' in df.columns:
            filtered_df = filtered_df[filtered_df['Score'] >= score_range]
        
        # Display filtered results
        st.write(f"Showing {len(filtered_df)} of {len(df)} results")
        
        # Configure display columns
        display_columns = self._get_display_columns(filtered_df)
        
        # Interactive dataframe with selection
        selected_rows = st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row"
        )
        
        return filtered_df, selected_rows
    
    def render_detailed_analysis(self, df: pd.DataFrame):
        """Render detailed analysis charts and insights."""
        if df.empty:
            return
            
        st.subheader("📈 Detailed Analysis")
        
        # Create tabs for different analysis views
        tab1, tab2, tab3, tab4 = st.tabs(["Score Analysis", "Evidence Analysis", "Geographic Insights", "Quality Metrics"])
        
        with tab1:
            self._render_score_analysis(df)
            
        with tab2:
            self._render_evidence_analysis(df)
            
        with tab3:
            self._render_geographic_analysis(df)
            
        with tab4:
            self._render_quality_metrics(df)
    
    def render_export_options(self, df: pd.DataFrame, result: WorkflowResult):
        """Render data export options with multiple formats."""
        st.subheader("📥 Export Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV export
            csv_data = self._prepare_csv_export(df)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"{result.segment}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col2:
            # Excel export
            excel_data = self._prepare_excel_export(df, result)
            st.download_button(
                label="📈 Download Excel",
                data=excel_data,
                file_name=f"{result.segment}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        with col3:
            # Summary report
            summary_data = self._prepare_summary_report(df, result)
            st.download_button(
                label="📝 Download Summary",
                data=summary_data,
                file_name=f"{result.segment}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    def _convert_to_dataframe(self, outputs: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert API results to pandas DataFrame."""
        if not outputs:
            return pd.DataFrame()
            
        # Normalize the data structure
        normalized_data = []
        for item in outputs:
            normalized_item = {
                'Organization': item.get('organization', ''),
                'Tier': item.get('tier', ''),
                'Score': item.get('score', 0),
                'Region': item.get('region', ''),
                'Evidence_URL': item.get('evidence_url', ''),
                'Notes': item.get('notes', ''),
                'Type': item.get('type', ''),
                'Facilities': item.get('facilities', ''),
                'EHR_Vendor': item.get('ehr_vendor', ''),
                'Confidence': item.get('confidence', 0)
            }
            normalized_data.append(normalized_item)
        
        return pd.DataFrame(normalized_data)
    
    def _get_display_columns(self, df: pd.DataFrame) -> List[str]:
        """Get optimized columns for display."""
        priority_columns = [
            'Organization', 'Tier', 'Score', 'Region', 
            'Type', 'EHR_Vendor', 'Confidence', 'Notes'
        ]
        
        available_columns = [col for col in priority_columns if col in df.columns]
        return available_columns
    
    def _render_tier_distribution(self, df: pd.DataFrame):
        """Render tier distribution chart with brand styling."""
        if 'Tier' not in df.columns or df.empty:
            return
            
        # Tier distribution chart with brand styling
        BrandComponents.section_header("Quality Distribution", "")
        
        tier_counts = df['Tier'].value_counts()
        tier_data = dict(tier_counts)
        
        # Create brand-compliant pie chart
        fig = ChartHelper.create_pie_chart(tier_data, "Results by Quality Tier")
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_regional_distribution(self, df: pd.DataFrame):
        """Render regional distribution chart with brand styling."""
        if 'Region' not in df.columns or df.empty:
            return
            
        # Regional distribution with brand styling
        BrandComponents.section_header("Geographic Distribution", "")
        
        region_counts = df['Region'].value_counts()
        region_data = dict(region_counts)
        
        # Create brand-compliant bar chart
        fig = ChartHelper.create_bar_chart(region_data, "Results by Region", "Region", "Count")
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_score_analysis(self, df: pd.DataFrame):
        """Render score distribution analysis."""
        if 'Score' not in df.columns or df.empty:
            st.info("Score data not available for this result set.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Score histogram
            fig = px.histogram(
                df, 
                x='Score', 
                nbins=20,
                title="Score Distribution",
                color_discrete_sequence=['#1f77b4']
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Score vs Tier scatter
            if 'Tier' in df.columns:
                fig = px.box(
                    df,
                    x='Tier',
                    y='Score',
                    color='Tier',
                    color_discrete_map=self.tier_colors,
                    title="Score by Tier"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_evidence_analysis(self, df: pd.DataFrame):
        """Render evidence quality analysis."""
        # Evidence URL availability
        evidence_available = df['Evidence_URL'].notna() & (df['Evidence_URL'] != '')
        evidence_stats = {
            'With Evidence': evidence_available.sum(),
            'Without Evidence': (~evidence_available).sum()
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                values=list(evidence_stats.values()),
                names=list(evidence_stats.keys()),
                title="Evidence Availability"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Top evidence domains
            if evidence_available.any():
                urls = df[evidence_available]['Evidence_URL'].dropna()
                domains = urls.str.extract(r'https?://([^/]+)')[0].value_counts().head(5)
                
                if not domains.empty:
                    fig = px.bar(
                        x=domains.values,
                        y=domains.index,
                        orientation='h',
                        title="Top Evidence Domains"
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
    
    def _render_geographic_analysis(self, df: pd.DataFrame):
        """Render geographic analysis."""
        if 'Region' not in df.columns:
            return
            
        # Regional quality distribution
        if 'Tier' in df.columns:
            regional_quality = df.groupby(['Region', 'Tier']).size().unstack(fill_value=0)
            
            fig = px.bar(
                regional_quality,
                title="Quality Distribution by Region",
                barmode='stack',
                color_discrete_map=self.tier_colors
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_quality_metrics(self, df: pd.DataFrame):
        """Render quality metrics and KPIs."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Quality Metrics**")
            
            # Calculate quality metrics
            total_results = len(df)
            if 'Tier' in df.columns:
                high_quality = len(df[df['Tier'].str.contains('Confirmed|Tier 1', case=False, na=False)])
                quality_rate = high_quality / total_results if total_results > 0 else 0
                
                st.metric("Quality Rate", f"{quality_rate:.1%}")
                st.metric("High Quality Count", high_quality)
            
            if 'Score' in df.columns:
                avg_score = df['Score'].mean()
                st.metric("Average Score", f"{avg_score:.1f}")
                
        with col2:
            st.write("**Coverage Metrics**")
            
            evidence_coverage = (df['Evidence_URL'].notna() & (df['Evidence_URL'] != '')).mean()
            st.metric("Evidence Coverage", f"{evidence_coverage:.1%}")
            
            if 'Region' in df.columns:
                region_diversity = len(df['Region'].unique())
                st.metric("Regional Diversity", region_diversity)
    
    def _prepare_csv_export(self, df: pd.DataFrame) -> str:
        """Prepare CSV export data."""
        return df.to_csv(index=False)
    
    def _prepare_excel_export(self, df: pd.DataFrame, result: WorkflowResult) -> bytes:
        """Prepare Excel export with multiple sheets."""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main results sheet
            df.to_excel(writer, sheet_name='Results', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': ['Total Results', 'Execution Time', 'Segment', 'Target Count'],
                'Value': [
                    len(df),
                    f"{result.execution_time:.1f}s" if hasattr(result, 'execution_time') else 'N/A',
                    result.segment.title(),
                    len(result.outputs)
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
        return output.getvalue()
    
    def _prepare_summary_report(self, df: pd.DataFrame, result: WorkflowResult) -> str:
        """Prepare text summary report."""
        report_lines = [
            f"ICP Discovery Engine - {result.segment.title()} Results Summary",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "OVERVIEW",
            "-" * 20,
            f"Total Organizations: {len(df)}",
            f"Segment: {result.segment.title()}",
        ]
        
        if 'Tier' in df.columns:
            tier_counts = df['Tier'].value_counts()
            report_lines.append("")
            report_lines.append("QUALITY BREAKDOWN")
            report_lines.append("-" * 20)
            for tier, count in tier_counts.items():
                report_lines.append(f"{tier}: {count}")
        
        if 'Region' in df.columns:
            region_counts = df['Region'].value_counts()
            report_lines.append("")
            report_lines.append("REGIONAL BREAKDOWN")
            report_lines.append("-" * 20)
            for region, count in region_counts.items():
                report_lines.append(f"{region}: {count}")
        
        if result.summary:
            report_lines.append("")
            report_lines.append("EXECUTION SUMMARY")
            report_lines.append("-" * 20)
            report_lines.append(result.summary)
        
        return "\n".join(report_lines)


def render_results_analyzer(workflow_result: Dict[str, Any]) -> None:
    """Render the complete results analysis interface with brand styling."""
    if not workflow_result:
        st.markdown("""
        <div style="background: rgba(71, 57, 231, 0.1); border-left: 4px solid #4739E7; padding: 16px; border-radius: 6px; margin: 16px 0;">
            <p style="color: #4739E7; font-family: Inter; font-weight: 400; margin: 0;">
                📝 No results to analyze. Run a workflow first.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    result = workflow_result["result"]
    analyzer = ResultsAnalyzer()
    
    # Results overview with brand styling
    df = analyzer.render_results_overview(result)
    
    if df is not None and not df.empty:
        # Brand divider
        st.markdown("""
        <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
        """, unsafe_allow_html=True)
        
        # Interactive table with brand styling
        filtered_df, selected_rows = analyzer.render_interactive_table(df)
        
        # Brand divider
        st.markdown("""
        <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
        """, unsafe_allow_html=True)
        
        # Detailed analysis with brand charts
        analyzer.render_detailed_analysis(filtered_df)
        
        # Brand divider
        st.markdown("""
        <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
        """, unsafe_allow_html=True)
        
        # Export options with brand styling
        analyzer.render_export_options(filtered_df, result)