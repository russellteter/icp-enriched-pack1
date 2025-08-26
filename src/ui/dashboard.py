"""
Main dashboard for ICP Discovery Engine.
Integrates all components into a cohesive business intelligence interface with brand styling.
"""

import streamlit as st
import time
from typing import Optional, Dict, Any

from .components.workflow_manager import render_workflow_manager
from .components.results_analyzer import render_results_analyzer
from .components.monitoring_panel import render_monitoring_panel
from .components.historical_viewer import render_historical_viewer
from .components.system_health_dashboard import render_system_health_dashboard
from .components.analytics_dashboard import render_analytics_dashboard
from .utils.api_client import get_api_client, display_api_error
from .assets.brand_components import BrandComponents
from .assets.logo import BrandLogo, LogoVariations


class ICPDashboard:
    """Main dashboard orchestrator."""
    
    def __init__(self):
        self.api_client = get_api_client()
        self._initialize_session_state()
        self._load_brand_styling()
        
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if "last_workflow_result" not in st.session_state:
            st.session_state.last_workflow_result = None
        if "dashboard_tab" not in st.session_state:
            st.session_state.dashboard_tab = "Discover"
        if "server_status" not in st.session_state:
            st.session_state.server_status = "unknown"
    
    def _load_brand_styling(self):
        """Load brand CSS and set favicon."""
        BrandComponents.load_brand_css()
        BrandLogo.set_page_favicon()
    
    def render_header(self):
        """Render dashboard header with brand logo and status indicators."""
        # Main container with brand styling
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 6, 2])
        
        with col1:
            # Brand logo
            BrandLogo.display_logo(size=80, show_text=False, style="default")
            
        with col2:
            # Title and subtitle with brand typography
            st.markdown("""
            <div style="padding: 20px 0; text-align: center;">
                <h1 style="color: #0A1849; font-weight: 300; font-size: 42px; margin-bottom: 8px; font-family: Inter;">
                    ICP Discovery Engine
                </h1>
                <p style="color: #0E0E1E; font-size: 18px; font-weight: 400; margin: 0; font-family: Inter;">
                    Advanced Business Intelligence for Target Client Discovery
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            # Status indicators and quick actions
            self._render_header_controls()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Divider with brand styling
        st.markdown("""
        <hr style="border: none; height: 1px; background: linear-gradient(90deg, #DAD7FA 0%, #4739E7 50%, #DAD7FA 100%); margin: 20px 0;">
        """, unsafe_allow_html=True)
    
    def render_navigation(self):
        """Render main navigation tabs with brand styling."""
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚀 Discover", 
            "📊 Analyze", 
            "📈 Monitor", 
            "📁 History",
            "🎯 Analytics"
        ])
        
        return tab1, tab2, tab3, tab4, tab5
    
    def _render_header_controls(self):
        """Render header control panel with status and actions."""
        # Server status with brand styling
        st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <p style="font-family: Inter; font-weight: 500; font-size: 14px; color: #0A1849; margin-bottom: 8px;">
                System Status
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Status indicator
        self._render_server_status()
        
        # Quick refresh action
        st.markdown("<br>", unsafe_allow_html=True)
        if BrandComponents.brand_button("🔄 Refresh", help="Refresh dashboard", key="header_refresh"):
            st.rerun()
    
    def render_discovery_tab(self):
        """Render the discovery workflow tab with brand styling."""
        # Section header with brand styling
        BrandComponents.section_header(
            "🎯 Target Discovery Workflow",
            "Configure and execute discovery workflows to find high-quality prospects"
        )
        
        # Quick stats overview in brand cards
        self._render_quick_stats()
        
        # Brand divider
        st.markdown("""
        <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
        """, unsafe_allow_html=True)
        
        # Workflow management
        workflow_result = render_workflow_manager()
        
        if workflow_result:
            st.session_state.last_workflow_result = workflow_result
            
            # Success message with brand styling
            st.markdown("""
            <div style="background: rgba(75, 181, 67, 0.1); border-left: 4px solid #4bb543; padding: 16px; border-radius: 6px; margin: 16px 0;">
                <p style="color: #4bb543; font-family: Inter; font-weight: 500; margin: 0;">
                    ✅ Workflow completed successfully! Switch to the 'Analyze' tab to view detailed results.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show quick preview with brand cards
            result = workflow_result["result"]
            if result.outputs:
                BrandComponents.section_header("📋 Quick Preview", "")
                
                # Quick stats with brand metrics
                stats = {}
                stats["Results Found"] = len(result.outputs)
                confirmed = sum(1 for o in result.outputs if o.get("tier", "").lower() in ["confirmed", "tier 1"])
                stats["High Quality"] = confirmed
                if result.budget:
                    total_resources = result.budget.get("searches", 0) + result.budget.get("fetches", 0)
                    stats["Resources Used"] = total_resources
                
                BrandComponents.quick_stats_grid(stats)
        
        # Tips and guidance
        self._render_discovery_tips()
    
    def render_analysis_tab(self):
        """Render the results analysis tab with brand styling."""
        BrandComponents.section_header(
            "📊 Results Analysis",
            "Analyze workflow results with interactive visualizations and detailed insights"
        )
        
        if st.session_state.last_workflow_result:
            render_results_analyzer(st.session_state.last_workflow_result)
        else:
            # Info message with brand styling
            st.markdown("""
            <div style="background: rgba(71, 57, 231, 0.1); border-left: 4px solid #4739E7; padding: 16px; border-radius: 6px; margin: 16px 0;">
                <p style="color: #4739E7; font-family: Inter; font-weight: 400; margin: 0;">
                    📝 No recent workflow results to analyze. Run a discovery workflow first in the 'Discover' tab.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show example of what analysis looks like
            self._render_analysis_preview()
    
    def render_monitoring_tab(self):
        """Render the system monitoring tab with comprehensive health dashboard."""
        # Use the comprehensive system health dashboard
        render_system_health_dashboard()
        
        # Brand divider
        st.markdown("""
        <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
        """, unsafe_allow_html=True)
        
        # Additional monitoring panel for backward compatibility
        render_monitoring_panel()
        
        # Brand divider
        st.markdown("""
        <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
        """, unsafe_allow_html=True)
        
        self._render_monitoring_insights()
    
    def render_history_tab(self):
        """Render the historical analysis tab with brand styling."""
        BrandComponents.section_header(
            "📁 Historical Analysis", 
            "Browse past workflow runs and analyze performance trends over time"
        )
        
        render_historical_viewer()
        
        # Brand divider
        st.markdown("""
        <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
        """, unsafe_allow_html=True)
        
        self._render_historical_insights()
    
    def render_analytics_tab(self):
        """Render the advanced analytics tab."""
        render_analytics_dashboard()
    
    def _render_server_status(self):
        """Render server status indicator with brand styling."""
        try:
            success, _ = self.api_client.health_check()
            if success:
                BrandComponents.status_indicator("online", "Online")
                st.session_state.server_status = "online"
            else:
                BrandComponents.status_indicator("offline", "Offline")
                st.session_state.server_status = "offline"
        except:
            BrandComponents.status_indicator("unknown", "Unknown")
            st.session_state.server_status = "unknown"
    
    def _render_quick_stats(self):
        """Render quick statistics overview with brand styling."""
        BrandComponents.section_header("📈 Quick Stats", "")
        
        # Try to get monitoring data
        success, dashboard_data = self.api_client.get_monitoring_dashboard()
        
        if success:
            today_data = dashboard_data.get("today", {})
            
            # Create stats dictionary for brand component
            stats = {}
            
            discoveries = today_data.get("discoveries", {})
            total_today = sum(discoveries.values()) if discoveries else 0
            stats["Today's Discoveries"] = total_today
            
            quality = today_data.get("quality", {})
            acceptance_rate = quality.get("acceptance_rate", 0)
            stats["Quality Rate"] = f"{acceptance_rate:.1%}"
            
            costs = today_data.get("costs", {})
            daily_cost = costs.get("total_usd", 0)
            stats["Daily Cost"] = f"${daily_cost:.2f}"
            
            alerts = dashboard_data.get("alerts", [])
            stats["Active Alerts"] = len(alerts)
            
            BrandComponents.quick_stats_grid(stats)
        else:
            # Fallback to basic metrics with brand styling
            stats = {
                "System Status": st.session_state.server_status.title(),
                "Available Segments": "3",
                "Discovery Modes": "2",
                "Target Regions": "3"
            }
            BrandComponents.quick_stats_grid(stats)
    
    def _render_discovery_tips(self):
        """Render discovery tips and best practices."""
        with st.expander("💡 Discovery Tips & Best Practices"):
            st.markdown("""
            **Getting Started:**
            - Start with smaller target counts (10-15) for faster results
            - Use "Fast" mode for quick exploration, "Deep" for comprehensive analysis
            - Healthcare typically yields 60-70% quality results
            - Corporate requires larger target counts for good coverage
            
            **Optimization Tips:**
            - Regional targeting (NA/EMEA) is faster than global searches
            - Deep mode provides 2x more comprehensive data but takes longer
            - Monitor resource usage to optimize budget allocation
            
            **Quality Indicators:**
            - Confirmed/Tier 1: Ready for immediate outreach
            - Probable/Tier 2: Requires additional validation
            - Tier 3: May need manual review
            """)
    
    def _render_analysis_preview(self):
        """Render preview of analysis capabilities with brand styling."""
        BrandComponents.section_header("🔍 Analysis Capabilities Preview", "")
        
        # Info box with brand styling
        st.markdown("""
        <div style="background: rgba(71, 57, 231, 0.1); border-left: 4px solid #4739E7; padding: 20px; border-radius: 6px; margin: 16px 0;">
            <h3 style="color: #0A1849; font-family: Inter; font-weight: 500; margin-bottom: 16px;">
                When you run a discovery workflow, you'll see:
            </h3>
            <ul style="color: #0E0E1E; font-family: Inter; margin: 0; padding-left: 20px;">
                <li style="margin-bottom: 8px;">📊 Interactive results table with filtering and sorting</li>
                <li style="margin-bottom: 8px;">📈 Quality distribution and geographic insights</li>
                <li style="margin-bottom: 8px;">🎯 Detailed scoring and evidence analysis</li>
                <li style="margin-bottom: 8px;">📥 Export options (CSV, Excel, Summary reports)</li>
                <li style="margin-bottom: 8px;">🔍 Advanced filtering by tier, region, and score</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Example metrics with brand styling
        stats = {
            "Example: Results Found": "15",
            "Example: High Quality": "9", 
            "Example: Avg Score": "84.2"
        }
        BrandComponents.quick_stats_grid(stats)
    
    def _render_monitoring_insights(self):
        """Render additional monitoring insights with brand styling."""
        BrandComponents.section_header("💡 Monitoring Insights", "")
        
        success, metrics = self.api_client.get_metrics()
        
        if success:
            # System config info with brand styling
            max_searches = metrics.get('budget', {}).get('max_searches', 'N/A')
            max_fetches = metrics.get('budget', {}).get('max_fetches', 'N/A')
            cache_ttl = metrics.get('cache', {}).get('ttl_seconds', 'N/A')
            
            st.markdown(f"""
            <div style="background: rgba(71, 57, 231, 0.1); border-left: 4px solid #4739E7; padding: 20px; border-radius: 6px; margin: 16px 0;">
                <h3 style="color: #0A1849; font-family: Inter; font-weight: 500; margin-bottom: 16px;">
                    System Configuration
                </h3>
                <ul style="color: #0E0E1E; font-family: Inter; margin: 0; padding-left: 20px;">
                    <li style="margin-bottom: 8px;">Max Searches per run: <strong>{max_searches}</strong></li>
                    <li style="margin-bottom: 8px;">Max Fetches per run: <strong>{max_fetches}</strong></li>
                    <li style="margin-bottom: 8px;">Cache TTL: <strong>{cache_ttl} seconds</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Performance tips with brand styling
        st.markdown("""
        <div style="background: rgba(255, 186, 0, 0.1); border-left: 4px solid #FFBA00; padding: 20px; border-radius: 6px; margin: 16px 0;">
            <h3 style="color: #0A1849; font-family: Inter; font-weight: 500; margin-bottom: 16px;">
                Performance Tips
            </h3>
            <ul style="color: #0E0E1E; font-family: Inter; margin: 0; padding-left: 20px;">
                <li style="margin-bottom: 8px;">Monitor cache hit rates for optimal performance</li>
                <li style="margin-bottom: 8px;">Watch for budget exhaustion in large runs</li>
                <li style="margin-bottom: 8px;">Check component health before critical workflows</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_historical_insights(self):
        """Render historical analysis insights with brand styling."""
        BrandComponents.section_header("📊 Historical Insights", "")
        
        # Historical features with brand styling
        st.markdown("""
        <div style="background: rgba(71, 57, 231, 0.1); border-left: 4px solid #4739E7; padding: 20px; border-radius: 6px; margin: 16px 0;">
            <h3 style="color: #0A1849; font-family: Inter; font-weight: 500; margin-bottom: 16px;">
                Historical Analysis Features
            </h3>
            <ul style="color: #0E0E1E; font-family: Inter; margin: 0; padding-left: 20px;">
                <li style="margin-bottom: 8px;">Compare performance across different runs</li>
                <li style="margin-bottom: 8px;">Track quality trends over time</li>
                <li style="margin-bottom: 8px;">Analyze efficiency patterns by segment</li>
                <li style="margin-bottom: 8px;">Export historical data for reporting</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Best practices with brand styling
        st.markdown("""
        <div style="background: rgba(75, 181, 67, 0.1); border-left: 4px solid #4bb543; padding: 20px; border-radius: 6px; margin: 16px 0;">
            <h3 style="color: #0A1849; font-family: Inter; font-weight: 500; margin-bottom: 16px;">
                Best Practices
            </h3>
            <ul style="color: #0E0E1E; font-family: Inter; margin: 0; padding-left: 20px;">
                <li style="margin-bottom: 8px;">Regular trend analysis helps optimize targeting</li>
                <li style="margin-bottom: 8px;">Compare similar segments for performance baselines</li>
                <li style="margin-bottom: 8px;">Use historical data to set realistic expectations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main dashboard application with brand styling."""
    # Page configuration with brand favicon
    st.set_page_config(
        page_title="ICP Discovery Engine",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize dashboard (loads brand CSS and favicon)
    dashboard = ICPDashboard()
    
    # Render header with brand styling
    dashboard.render_header()
    
    # Render navigation with brand tabs
    tab1, tab2, tab3, tab4, tab5 = dashboard.render_navigation()
    
    # Render tab content
    with tab1:
        dashboard.render_discovery_tab()
        
    with tab2:
        dashboard.render_analysis_tab()
        
    with tab3:
        dashboard.render_monitoring_tab()
        
    with tab4:
        dashboard.render_history_tab()
    
    with tab5:
        dashboard.render_analytics_tab()
    
    # Brand footer
    st.markdown("""
    <div style="margin-top: 40px; padding: 20px 0; border-top: 1px solid #DAD7FA; text-align: center;">
        <p style="color: #0E0E1E; font-family: Inter; font-size: 14px; margin: 0;">
            ICP Discovery Engine v2.0 | Powered by LangGraph & FastAPI
        </p>
        <p style="color: #4739E7; font-family: Inter; font-size: 12px; margin: 8px 0 0 0;">
            Designed with ❤️ using the ICP brand system
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()