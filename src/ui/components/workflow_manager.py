"""
Advanced workflow management component for ICP Discovery Engine.
Provides parameter configuration, validation, execution, and progress tracking with brand styling.
"""

import streamlit as st
import time
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

from ..utils.api_client import get_api_client, RunRequest, Segment, Mode, Region, display_api_error, format_budget_display, format_execution_time
from ..assets.brand_components import BrandComponents


class WorkflowManager:
    """Advanced workflow management with validation and progress tracking."""
    
    def __init__(self):
        self.api_client = get_api_client()
        
    def render_configuration_panel(self) -> RunRequest:
        """Render workflow configuration panel with brand styling and validation."""
        # Configuration panel in a brand card
        st.markdown("""
        <div class="brand-card">
            <div class="brand-card-header">
                🎯 Workflow Configuration
            </div>
        """, unsafe_allow_html=True)
        
        # Create two columns for better layout
        col1, col2 = st.columns(2)
        
        with col1:
            # Segment selection with descriptions
            segment_options = {
                "Healthcare EHR & Training": Segment.HEALTHCARE,
                "Corporate Academies": Segment.CORPORATE,
                "Training Providers": Segment.PROVIDERS
            }
            
            segment_choice = st.selectbox(
                "Target Segment",
                options=list(segment_options.keys()),
                help=self._get_segment_help_text()
            )
            segment = segment_options[segment_choice]
            
            # Target count with smart defaults
            target_count = st.number_input(
                "Target Count",
                min_value=1,
                max_value=100,
                value=self._get_default_target_count(segment),
                help="Number of organizations to discover. Larger counts take longer but provide more comprehensive results."
            )
            
        with col2:
            # Mode selection with resource implications
            mode_options = {
                "Fast Discovery": Mode.FAST,
                "Deep Analysis": Mode.DEEP
            }
            
            mode_choice = st.selectbox(
                "Discovery Mode",
                options=list(mode_options.keys()),
                help=self._get_mode_help_text()
            )
            mode = mode_options[mode_choice]
            
            # Region selection
            region_options = {
                "North America": Region.NA,
                "Europe/Middle East": Region.EMEA,
                "Global": Region.BOTH
            }
            
            region_choice = st.selectbox(
                "Target Region",
                options=list(region_options.keys()),
                help="Geographic focus for discovery. Global searches take longer but provide broader coverage."
            )
            region = region_options[region_choice]
        
        # Resource estimation with brand styling
        self._display_resource_estimation(target_count, mode, region)
        
        # Close the configuration card
        st.markdown("</div>", unsafe_allow_html=True)
        
        return RunRequest(
            segment=segment,
            targetcount=target_count,
            mode=mode,
            region=region
        )
    
    def execute_workflow(self, request: RunRequest) -> Optional[Dict[str, Any]]:
        """Execute workflow with progress tracking and error handling."""
        # Pre-flight checks
        if not self._pre_flight_checks():
            return None
            
        # Create progress tracking with brand styling
        st.markdown("""
        <div class="brand-card">
            <div class="brand-card-header">
                ⚡ Workflow Execution
            </div>
        """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        metrics_container = st.empty()
        
        # Initialize execution with brand styling
        st.markdown("""
        <p style="color: #4739E7; font-family: Inter; font-weight: 500; margin: 16px 0;">
            🚀 Initializing workflow...
        </p>
        """, unsafe_allow_html=True)
        progress_bar.progress(10)
        
        # Execute workflow
        start_time = time.time()
        st.markdown("""
        <p style="color: #4739E7; font-family: Inter; font-weight: 500; margin: 16px 0;">
            ⚡ Executing discovery workflow...
        </p>
        """, unsafe_allow_html=True)
        progress_bar.progress(30)
        
        # Show estimated time with brand styling
        estimated_time = self._estimate_execution_time(request)
        st.markdown(f"""
        <p style="color: #0E0E1E; font-family: Inter; font-weight: 400; margin: 16px 0;">
            ⏱️ Estimated completion: ~{estimated_time}
        </p>
        """, unsafe_allow_html=True)
        
        # Make API call
        success, result = self.api_client.run_workflow(request)
        
        if success:
            progress_bar.progress(100)
            st.markdown("""
            <p style="color: #4bb543; font-family: Inter; font-weight: 500; margin: 16px 0;">
                ✅ Workflow completed successfully!
            </p>
            """, unsafe_allow_html=True)
            
            # Display execution summary
            execution_time = time.time() - start_time
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Organizations Found", result.count)
            with col2:
                st.metric("Execution Time", format_execution_time(execution_time))
            with col3:
                confirmed_count = sum(1 for o in result.outputs if o.get("tier") == "Confirmed")
                st.metric("Confirmed Tier", confirmed_count)
            
            # Display budget usage
            if result.budget:
                st.subheader("📊 Resource Usage")
                budget_metrics = format_budget_display(result.budget)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Searches", budget_metrics["Searches"])
                with col2:
                    st.metric("Fetches", budget_metrics["Fetches"])
                with col3:
                    st.metric("Enrichments", budget_metrics["Enrichments"])
                with col4:
                    st.metric("LLM Tokens", budget_metrics["Tokens"])
            
            # Display summary if available with brand styling
            if result.summary:
                st.markdown(f"""
                <div style="background: rgba(71, 57, 231, 0.1); border-left: 4px solid #4739E7; padding: 16px; border-radius: 6px; margin: 16px 0;">
                    <p style="color: #4739E7; font-family: Inter; font-weight: 400; margin: 0;">
                        📝 <strong>Summary:</strong> {result.summary}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # Close the execution card
            st.markdown("</div>", unsafe_allow_html=True)
            
            return {
                "result": result,
                "execution_time": execution_time,
                "request": request
            }
            
        else:
            progress_bar.progress(0)
            st.markdown("""
            <p style="color: #ff4d4d; font-family: Inter; font-weight: 500; margin: 16px 0;">
                ❌ Workflow failed
            </p>
            """, unsafe_allow_html=True)
            display_api_error(result, "Workflow Execution")
            
            # Close the execution card
            st.markdown("</div>", unsafe_allow_html=True)
            
            return None
    
    def _pre_flight_checks(self) -> bool:
        """Perform pre-flight checks before workflow execution."""
        st.write("🔍 **Pre-flight Checks**")
        
        # Check server connection
        with st.spinner("Checking server connection..."):
            success, health = self.api_client.health_check()
            
        if success:
            st.success("✅ Server connection established")
            return True
        else:
            st.error("❌ Server connection failed")
            display_api_error(health, "Health Check")
            return False
    
    def _get_segment_help_text(self) -> str:
        """Get help text for segment selection."""
        return """
        **Healthcare**: EHR providers with active training programs
        **Corporate**: Large enterprises (7,500+ employees) with named academies  
        **Providers**: B2B training companies with live virtual instruction
        """
    
    def _get_mode_help_text(self) -> str:
        """Get help text for mode selection."""
        return """
        **Fast Discovery**: Standard resource usage, quicker results
        **Deep Analysis**: 2x searches/fetches, more comprehensive data
        """
    
    def _get_default_target_count(self, segment: Segment) -> int:
        """Get smart default target count based on segment."""
        defaults = {
            Segment.HEALTHCARE: 15,
            Segment.CORPORATE: 10,
            Segment.PROVIDERS: 20
        }
        return defaults.get(segment, 10)
    
    def _display_resource_estimation(self, target_count: int, mode: Mode, region: Region):
        """Display estimated resource usage for configuration."""
        # Calculate estimates
        base_searches = target_count * 3
        base_fetches = target_count * 4
        base_enrichments = target_count * 1
        
        # Apply mode multipliers
        if mode == Mode.DEEP:
            base_searches *= 2
            base_fetches *= 2
            base_enrichments = int(base_enrichments * 1.5)
        
        # Apply region multipliers
        if region == Region.BOTH:
            base_searches = int(base_searches * 1.3)
            base_fetches = int(base_fetches * 1.3)
        
        # Estimate time
        estimated_minutes = (base_searches * 2 + base_fetches * 1 + base_enrichments * 5) / 60
        
        # Display estimation
        st.info(f"""
        📈 **Resource Estimation**
        - Searches: ~{base_searches}
        - Fetches: ~{base_fetches}  
        - Enrichments: ~{base_enrichments}
        - Estimated time: ~{estimated_minutes:.0f} minutes
        """)
    
    def _estimate_execution_time(self, request: RunRequest) -> str:
        """Estimate workflow execution time."""
        base_minutes = request.targetcount * 0.5
        
        if request.mode == Mode.DEEP:
            base_minutes *= 2
            
        if request.region == Region.BOTH:
            base_minutes *= 1.3
            
        if base_minutes < 2:
            return "1-2 minutes"
        elif base_minutes < 5:
            return f"{int(base_minutes)}-{int(base_minutes + 1)} minutes"
        else:
            return f"~{int(base_minutes)} minutes"
    
    def render_quick_actions(self):
        """Render quick action buttons for common workflows."""
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏥 Quick Healthcare", help="Fast healthcare discovery (15 targets, NA region)"):
                request = RunRequest(
                    segment=Segment.HEALTHCARE,
                    targetcount=15,
                    mode=Mode.FAST,
                    region=Region.NA
                )
                return self.execute_workflow(request)
        
        with col2:
            if st.button("🏢 Quick Corporate", help="Fast corporate discovery (10 targets, Global)"):
                request = RunRequest(
                    segment=Segment.CORPORATE,
                    targetcount=10,
                    mode=Mode.FAST,
                    region=Region.BOTH
                )
                return self.execute_workflow(request)
        
        with col3:
            if st.button("📚 Quick Providers", help="Fast provider discovery (20 targets, NA region)"):
                request = RunRequest(
                    segment=Segment.PROVIDERS,
                    targetcount=20,
                    mode=Mode.FAST,
                    region=Region.NA
                )
                return self.execute_workflow(request)
        
        return None


def render_workflow_manager() -> Optional[Dict[str, Any]]:
    """Render the complete workflow management interface with brand styling."""
    manager = WorkflowManager()
    
    # Configuration panel (already has brand styling)
    request = manager.render_configuration_panel()
    
    # Brand divider
    st.markdown("""
    <div style="margin: 24px 0; height: 1px; background: #DAD7FA;"></div>
    """, unsafe_allow_html=True)
    
    # Execution controls with brand styling
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Primary execution button with brand styling
        if BrandComponents.brand_button("🚀 Execute Workflow", key="execute_workflow", variant="primary"):
            return manager.execute_workflow(request)
    
    with col2:
        # Quick actions
        quick_result = manager.render_quick_actions()
        if quick_result:
            return quick_result
    
    return None