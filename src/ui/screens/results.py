"""
Modern results view for ICP Discovery Engine.
Clean, focused display of discovery results with actionable insights.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from components.modern_components import ModernComponents, ModernNavigation


def render_results_screen():
    """Render the clean, focused results view."""
    
    # Check if we have results to display
    if "discovery_result" not in st.session_state:
        render_no_results_state()
        return
    
    result = st.session_state.discovery_result
    outputs = result.get("outputs", [])
    
    if not outputs:
        render_empty_results_state()
        return
    
    render_results_dashboard(result, outputs)


def render_no_results_state():
    """Show state when no results are available."""
    st.markdown('<div class="modern-container" style="padding-top: var(--space-16);">', unsafe_allow_html=True)
    
    ModernComponents.empty_state(
        title="No Results to Show",
        description="You haven't run a discovery yet. Let's get started and find your ideal customers.",
        action_text="Start Discovery",
        action_key="start_new_discovery"
    )
    
    if st.session_state.get("start_new_discovery", False):
        ModernNavigation.navigate_to("setup")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_empty_results_state():
    """Show state when discovery returned no results."""
    st.markdown('<div class="modern-container" style="padding-top: var(--space-16);">', unsafe_allow_html=True)
    
    ModernComponents.empty_state(
        title="No Organizations Found",
        description="Your search didn't return any results. Try adjusting your criteria or expanding your search scope.",
        action_text="Try Different Settings",
        action_key="try_different_settings"
    )
    
    if st.session_state.get("try_different_settings", False):
        ModernNavigation.navigate_to("setup")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_results_dashboard(result: Dict[str, Any], outputs: List[Dict[str, Any]]):
    """Render the main results dashboard."""
    
    # Header with results summary
    render_results_header(result, outputs)
    
    # Main results content
    st.markdown('<div class="modern-container">', unsafe_allow_html=True)
    
    # Tab-like navigation for different views
    view_tab = render_view_selector()
    
    if view_tab == "Overview":
        render_overview_tab(outputs)
    elif view_tab == "High Quality":
        render_high_quality_tab(outputs)
    elif view_tab == "All Results":
        render_all_results_tab(outputs)
    elif view_tab == "Export":
        render_export_tab(result, outputs)
    
    # Action buttons at bottom
    render_bottom_actions()
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_results_header(result: Dict[str, Any], outputs: List[Dict[str, Any]]):
    """Render the results header with key metrics."""
    
    # Calculate key metrics
    total_found = len(outputs)
    confirmed = len([o for o in outputs if o.get("tier") == "Confirmed"])
    probable = len([o for o in outputs if o.get("tier") == "Probable"])
    avg_score = sum(o.get("score", 0) for o in outputs) / max(total_found, 1)
    
    # Segment display name
    segment_names = {
        "healthcare": "Healthcare EHR & Training",
        "corporate": "Corporate Learning Academies",
        "providers": "Professional Training Providers"
    }
    segment_name = segment_names.get(result.get("segment", ""), result.get("segment", "").title())
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%); color: white; padding: var(--space-12) 0;">
        <div class="modern-container">
            <div style="text-align: center; margin-bottom: var(--space-8);">
                <h1 style="color: white; margin-bottom: var(--space-2); font-size: var(--font-size-3xl);">
                    Discovery Results: {segment_name}
                </h1>
                <p style="color: rgba(255,255,255,0.8); font-size: var(--font-size-lg);">
                    Found {total_found} organizations matching your criteria
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--space-6);">
                <div style="text-align: center; background: rgba(255,255,255,0.1); padding: var(--space-6); border-radius: var(--border-radius-lg);">
                    <div style="font-size: var(--font-size-3xl); font-weight: 600; margin-bottom: var(--space-2);">{confirmed}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: var(--font-size-sm);">High Quality</div>
                </div>
                <div style="text-align: center; background: rgba(255,255,255,0.1); padding: var(--space-6); border-radius: var(--border-radius-lg);">
                    <div style="font-size: var(--font-size-3xl); font-weight: 600; margin-bottom: var(--space-2);">{probable}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: var(--font-size-sm);">Probable Matches</div>
                </div>
                <div style="text-align: center; background: rgba(255,255,255,0.1); padding: var(--space-6); border-radius: var(--border-radius-lg);">
                    <div style="font-size: var(--font-size-3xl); font-weight: 600; margin-bottom: var(--space-2);">{int(avg_score)}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: var(--font-size-sm);">Avg Quality Score</div>
                </div>
                <div style="text-align: center; background: rgba(255,255,255,0.1); padding: var(--space-6); border-radius: var(--border-radius-lg);">
                    <div style="font-size: var(--font-size-3xl); font-weight: 600; margin-bottom: var(--space-2);">{int((confirmed/total_found)*100) if total_found > 0 else 0}%</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: var(--font-size-sm);">Success Rate</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_view_selector() -> str:
    """Render view selector tabs and return selected view."""
    st.markdown('<div style="padding: var(--space-8) 0;">', unsafe_allow_html=True)
    
    # Tab-like selector using buttons
    col1, col2, col3, col4 = st.columns(4)
    
    if "results_view" not in st.session_state:
        st.session_state.results_view = "Overview"
    
    with col1:
        if st.button("📊 Overview", key="view_overview", help="Summary and key insights"):
            st.session_state.results_view = "Overview"
    
    with col2:
        if st.button("⭐ High Quality", key="view_high_quality", help="Top-tier prospects"):
            st.session_state.results_view = "High Quality"
    
    with col3:
        if st.button("📋 All Results", key="view_all", help="Complete results list"):
            st.session_state.results_view = "All Results"
    
    with col4:
        if st.button("📤 Export", key="view_export", help="Download and export options"):
            st.session_state.results_view = "Export"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return st.session_state.results_view


def render_overview_tab(outputs: List[Dict[str, Any]]):
    """Render the overview tab with key insights."""
    
    # Quality distribution chart
    confirmed = len([o for o in outputs if o.get("tier") == "Confirmed"])
    probable = len([o for o in outputs if o.get("tier") == "Probable"])
    excluded = len([o for o in outputs if o.get("tier") not in ["Confirmed", "Probable"]])
    
    ModernComponents.modern_card(f"""
    <h3 style="margin-bottom: var(--space-4); color: var(--gray-900);">Quality Distribution</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-6);">
        <div style="text-align: center; padding: var(--space-4); background: var(--gray-50); border-radius: var(--border-radius);">
            <div style="font-size: var(--font-size-2xl); font-weight: 600; color: var(--success); margin-bottom: var(--space-2);">{confirmed}</div>
            <div style="color: var(--gray-600);">Confirmed Matches</div>
            <div style="font-size: var(--font-size-sm); color: var(--gray-500); margin-top: var(--space-1);">Ready for outreach</div>
        </div>
        <div style="text-align: center; padding: var(--space-4); background: var(--gray-50); border-radius: var(--border-radius);">
            <div style="font-size: var(--font-size-2xl); font-weight: 600; color: var(--warning); margin-bottom: var(--space-2);">{probable}</div>
            <div style="color: var(--gray-600);">Probable Matches</div>
            <div style="font-size: var(--font-size-sm); color: var(--gray-500); margin-top: var(--space-1);">Needs verification</div>
        </div>
        {f'<div style="text-align: center; padding: var(--space-4); background: var(--gray-50); border-radius: var(--border-radius);"><div style="font-size: var(--font-size-2xl); font-weight: 600; color: var(--gray-400); margin-bottom: var(--space-2);">{excluded}</div><div style="color: var(--gray-600);">Excluded</div><div style="font-size: var(--font-size-sm); color: var(--gray-500); margin-top: var(--space-1);">Didn\'t meet criteria</div></div>' if excluded > 0 else ''}
    </div>
    """)
    
    # Top prospects preview
    if confirmed > 0:
        top_prospects = sorted([o for o in outputs if o.get("tier") == "Confirmed"], 
                              key=lambda x: x.get("score", 0), reverse=True)[:3]
        
        ModernComponents.modern_card(f"""
        <h3 style="margin-bottom: var(--space-4); color: var(--gray-900);">Top Prospects</h3>
        <div style="space-y: var(--space-4);">
            {''.join([render_prospect_card(prospect, compact=True) for prospect in top_prospects])}
        </div>
        """)
    
    # Quick insights
    insights = generate_insights(outputs)
    if insights:
        ModernComponents.modern_card(f"""
        <h3 style="margin-bottom: var(--space-4); color: var(--gray-900);">Key Insights</h3>
        <div style="space-y: var(--space-3);">
            {''.join([f'<div style="display: flex; align-items: center; margin-bottom: var(--space-2);"><span style="color: var(--primary); margin-right: var(--space-2);">•</span><span style="color: var(--gray-700);">{insight}</span></div>' for insight in insights])}
        </div>
        """)


def render_high_quality_tab(outputs: List[Dict[str, Any]]):
    """Render high quality prospects tab."""
    
    confirmed_prospects = [o for o in outputs if o.get("tier") == "Confirmed"]
    confirmed_prospects.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    if not confirmed_prospects:
        ModernComponents.empty_state(
            title="No High Quality Matches",
            description="No organizations met the high quality criteria. Check the 'All Results' tab for probable matches.",
            action_text="View All Results",
            action_key="view_all_from_hq"
        )
        
        if st.session_state.get("view_all_from_hq", False):
            st.session_state.results_view = "All Results"
            st.rerun()
        return
    
    st.markdown(f"""
    <div style="margin-bottom: var(--space-6);">
        <h3 style="color: var(--gray-900); margin-bottom: var(--space-2);">
            {len(confirmed_prospects)} High Quality Prospects
        </h3>
        <p style="color: var(--gray-600);">
            These organizations closely match your ideal customer profile and are ready for outreach.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render each prospect
    for prospect in confirmed_prospects:
        render_detailed_prospect_card(prospect)


def render_all_results_tab(outputs: List[Dict[str, Any]]):
    """Render all results in a sortable, filterable table."""
    
    st.markdown(f"""
    <div style="margin-bottom: var(--space-6);">
        <h3 style="color: var(--gray-900); margin-bottom: var(--space-2);">
            All {len(outputs)} Results
        </h3>
        <p style="color: var(--gray-600);">
            Complete list of organizations found, sorted by quality score.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        tier_filter = st.selectbox(
            "Filter by quality:",
            options=["All", "Confirmed", "Probable", "Excluded"],
            index=0,
            key="tier_filter"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by:",
            options=["Score (High to Low)", "Score (Low to High)", "Organization Name"],
            index=0,
            key="sort_filter"
        )
    
    # Apply filters and sorting
    filtered_outputs = outputs
    if tier_filter != "All":
        filtered_outputs = [o for o in outputs if o.get("tier") == tier_filter]
    
    if sort_by == "Score (High to Low)":
        filtered_outputs.sort(key=lambda x: x.get("score", 0), reverse=True)
    elif sort_by == "Score (Low to High)":
        filtered_outputs.sort(key=lambda x: x.get("score", 0))
    elif sort_by == "Organization Name":
        filtered_outputs.sort(key=lambda x: x.get("organization", ""))
    
    # Results table
    if filtered_outputs:
        df = pd.DataFrame(filtered_outputs)
        
        # Display key columns in a clean format
        display_columns = ["organization", "tier", "score"]
        if "industry" in df.columns:
            display_columns.append("industry")
        if "region" in df.columns:
            display_columns.append("region")
        if "evidence_url" in df.columns:
            display_columns.append("evidence_url")
        
        # Filter to existing columns
        display_columns = [col for col in display_columns if col in df.columns]
        
        st.dataframe(
            df[display_columns],
            use_container_width=True,
            hide_index=True
        )
    else:
        ModernComponents.status_message(
            message=f"No results match the filter '{tier_filter}'",
            status_type="info"
        )


def render_export_tab(result: Dict[str, Any], outputs: List[Dict[str, Any]]):
    """Render export options tab."""
    
    st.markdown("""
    <div style="margin-bottom: var(--space-6);">
        <h3 style="color: var(--gray-900); margin-bottom: var(--space-2);">Export Your Results</h3>
        <p style="color: var(--gray-600);">Download your discovery results in various formats for further analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        ModernComponents.modern_card("""
        <h4 style="color: var(--gray-900); margin-bottom: var(--space-4);">📊 CSV Export</h4>
        <p style="color: var(--gray-600); margin-bottom: var(--space-4); font-size: var(--font-size-sm);">
            Export all results as a CSV file for analysis in Excel, Google Sheets, or your CRM.
        </p>
        """)
        
        if st.button("📥 Download CSV", key="download_csv", help="Download results as CSV"):
            csv_data = pd.DataFrame(outputs).to_csv(index=False)
            st.download_button(
                label="Save CSV File",
                data=csv_data,
                file_name=f"icp_discovery_{result.get('segment', 'results')}.csv",
                mime="text/csv",
                key="csv_download_button"
            )
    
    with col2:
        ModernComponents.modern_card("""
        <h4 style="color: var(--gray-900); margin-bottom: var(--space-4);">📋 Summary Report</h4>
        <p style="color: var(--gray-600); margin-bottom: var(--space-4); font-size: var(--font-size-sm);">
            Generate a formatted summary report with key insights and top prospects.
        </p>
        """)
        
        if st.button("📄 Generate Report", key="generate_report", help="Create summary report"):
            report_content = generate_summary_report(result, outputs)
            st.download_button(
                label="Save Report",
                data=report_content,
                file_name=f"icp_discovery_report_{result.get('segment', 'results')}.txt",
                mime="text/plain",
                key="report_download_button"
            )
    
    # Budget and cost summary
    budget = result.get("budget", {})
    if budget:
        ModernComponents.modern_card(f"""
        <h4 style="color: var(--gray-900); margin-bottom: var(--space-4);">💰 Resource Usage</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: var(--space-4);">
            <div style="text-align: center;">
                <div style="font-weight: 500; color: var(--primary);">{budget.get('searches', 0)}</div>
                <div style="font-size: var(--font-size-sm); color: var(--gray-600);">Searches</div>
            </div>
            <div style="text-align: center;">
                <div style="font-weight: 500; color: var(--primary);">{budget.get('fetches', 0)}</div>
                <div style="font-size: var(--font-size-sm); color: var(--gray-600);">Web Fetches</div>
            </div>
            <div style="text-align: center;">
                <div style="font-weight: 500; color: var(--primary);">{budget.get('enrich', 0)}</div>
                <div style="font-size: var(--font-size-sm); color: var(--gray-600);">Enrichments</div>
            </div>
        </div>
        """)


def render_bottom_actions():
    """Render action buttons at the bottom of results page."""
    st.markdown('<div style="padding: var(--space-8) 0; border-top: 1px solid var(--gray-200); margin-top: var(--space-8);">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Home", key="results_home", help="Return to home screen"):
            # Clear all session state
            for key in ["discovery_result", "discovery_request", "execution_state", "results_view"]:
                if key in st.session_state:
                    del st.session_state[key]
            ModernNavigation.navigate_to("home")
    
    with col2:
        if st.button("🔄 New Discovery", key="results_new", help="Start a new discovery"):
            # Clear execution/result state but keep other preferences
            for key in ["discovery_result", "discovery_request", "execution_state", "results_view"]:
                if key in st.session_state:
                    del st.session_state[key]
            ModernNavigation.navigate_to("setup")
    
    with col3:
        if st.button("⚙️ Refine Search", key="results_refine", help="Modify current search parameters"):
            # Keep current request for modification
            ModernNavigation.navigate_to("setup")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_prospect_card(prospect: Dict[str, Any], compact: bool = False) -> str:
    """Generate HTML for a single prospect card."""
    
    organization = prospect.get("organization", "Unknown Organization")
    tier = prospect.get("tier", "Unknown")
    score = prospect.get("score", 0)
    
    tier_colors = {
        "Confirmed": "var(--success)",
        "Probable": "var(--warning)",
        "Excluded": "var(--gray-400)"
    }
    
    tier_color = tier_colors.get(tier, "var(--gray-400)")
    
    card_class = "compact-card" if compact else "full-card"
    
    return f"""
    <div style="border: 1px solid var(--gray-200); border-radius: var(--border-radius); padding: var(--space-4); margin-bottom: var(--space-3); background: var(--white);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="color: var(--gray-900); margin: 0;">{organization}</h4>
            <div style="display: flex; align-items: center; gap: var(--space-3);">
                <span style="background: {tier_color}; color: var(--white); padding: var(--space-1) var(--space-3); border-radius: var(--border-radius); font-size: var(--font-size-sm); font-weight: 500;">{tier}</span>
                <span style="color: var(--gray-600); font-weight: 500;">Score: {score}</span>
            </div>
        </div>
    </div>
    """


def render_detailed_prospect_card(prospect: Dict[str, Any]):
    """Render a detailed prospect card with all available information."""
    
    organization = prospect.get("organization", "Unknown Organization")
    tier = prospect.get("tier", "Unknown")
    score = prospect.get("score", 0)
    industry = prospect.get("industry", "")
    region = prospect.get("region", "")
    evidence_url = prospect.get("evidence_url", "")
    notes = prospect.get("notes", "")
    
    tier_colors = {
        "Confirmed": "var(--success)",
        "Probable": "var(--warning)",
        "Excluded": "var(--gray-400)"
    }
    tier_color = tier_colors.get(tier, "var(--gray-400)")
    
    card_html = f"""
    <div style="border: 1px solid var(--gray-200); border-radius: var(--border-radius-lg); padding: var(--space-6); margin-bottom: var(--space-4); background: var(--white); box-shadow: var(--shadow-sm);">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: var(--space-4);">
            <div>
                <h3 style="color: var(--gray-900); margin: 0; margin-bottom: var(--space-2);">{organization}</h3>
                {f'<p style="color: var(--gray-600); margin: 0; font-size: var(--font-size-sm);">{industry}</p>' if industry else ''}
            </div>
            <div style="text-align: right;">
                <div style="background: {tier_color}; color: var(--white); padding: var(--space-2) var(--space-4); border-radius: var(--border-radius); font-weight: 500; margin-bottom: var(--space-2);">{tier}</div>
                <div style="color: var(--gray-600); font-weight: 500;">Quality Score: {score}</div>
            </div>
        </div>
        
        {f'<div style="margin-bottom: var(--space-3);"><span style="color: var(--gray-600); font-size: var(--font-size-sm);">Region:</span> <span style="color: var(--gray-900);">{region}</span></div>' if region else ''}
        
        {f'<div style="margin-bottom: var(--space-3); padding: var(--space-3); background: var(--gray-50); border-radius: var(--border-radius);"><div style="color: var(--gray-700); font-size: var(--font-size-sm);">{notes}</div></div>' if notes else ''}
        
        {f'<div style="margin-top: var(--space-4);"><a href="{evidence_url}" target="_blank" style="color: var(--primary); text-decoration: none; font-size: var(--font-size-sm);">🔗 View Evidence</a></div>' if evidence_url else ''}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)


def generate_insights(outputs: List[Dict[str, Any]]) -> List[str]:
    """Generate key insights from the results."""
    if not outputs:
        return []
    
    insights = []
    
    # Quality insights
    confirmed = len([o for o in outputs if o.get("tier") == "Confirmed"])
    total = len(outputs)
    
    if confirmed / total >= 0.6:
        insights.append("Strong quality results - over 60% are high-confidence matches")
    elif confirmed / total >= 0.3:
        insights.append("Good quality mix - solid foundation of confirmed prospects")
    elif confirmed == 0:
        insights.append("No confirmed matches - consider broadening search criteria")
    
    # Score insights
    scores = [o.get("score", 0) for o in outputs]
    avg_score = sum(scores) / len(scores)
    
    if avg_score >= 85:
        insights.append("Excellent average quality score - prospects are well-matched")
    elif avg_score >= 70:
        insights.append("Good average quality score - prospects show strong potential")
    
    # Regional insights if available
    regions = [o.get("region", "") for o in outputs if o.get("region")]
    if regions:
        region_counts = {region: regions.count(region) for region in set(regions)}
        dominant_region = max(region_counts, key=region_counts.get)
        insights.append(f"Most prospects found in {dominant_region.upper()} region")
    
    return insights[:3]  # Limit to 3 key insights


def generate_summary_report(result: Dict[str, Any], outputs: List[Dict[str, Any]]) -> str:
    """Generate a text summary report."""
    
    segment = result.get("segment", "Unknown")
    total = len(outputs)
    confirmed = len([o for o in outputs if o.get("tier") == "Confirmed"])
    probable = len([o for o in outputs if o.get("tier") == "Probable"])
    
    report = f"""
ICP DISCOVERY RESULTS REPORT
===========================

Segment: {segment.title()}
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
-------
Total Organizations Found: {total}
High Quality Matches: {confirmed}
Probable Matches: {probable}
Success Rate: {int((confirmed/total)*100) if total > 0 else 0}%

TOP PROSPECTS
-------------
"""
    
    top_prospects = sorted([o for o in outputs if o.get("tier") == "Confirmed"], 
                          key=lambda x: x.get("score", 0), reverse=True)[:5]
    
    for i, prospect in enumerate(top_prospects, 1):
        report += f"""
{i}. {prospect.get('organization', 'Unknown')}
   Quality Score: {prospect.get('score', 0)}
   Tier: {prospect.get('tier', 'Unknown')}
   {f"Industry: {prospect.get('industry', '')}" if prospect.get('industry') else ''}
   {f"Region: {prospect.get('region', '')}" if prospect.get('region') else ''}
   {f"Evidence: {prospect.get('evidence_url', '')}" if prospect.get('evidence_url') else ''}
"""
    
    # Add resource usage if available
    budget = result.get("budget", {})
    if budget:
        report += f"""

RESOURCE USAGE
--------------
Search Queries: {budget.get('searches', 0)}
Web Pages Fetched: {budget.get('fetches', 0)}
Data Enrichments: {budget.get('enrich', 0)}
"""
    
    return report