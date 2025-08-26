"""
Modern progress/execution screen for ICP Discovery Engine.
Elegant progress tracking with real-time updates and clean status display.
"""

import streamlit as st
import time
import requests
import json
from typing import Optional, Dict, List
from components.modern_components import ModernComponents, ModernNavigation
from utils.api_client import RunRequest


def render_progress_screen():
    """Render the elegant progress tracking screen."""
    
    # Check if we have a discovery request to run
    if "discovery_request" not in st.session_state:
        render_no_request_state()
        return
    
    # Initialize execution state
    if "execution_state" not in st.session_state:
        st.session_state.execution_state = "not_started"
        st.session_state.current_step = None
        st.session_state.completed_steps = []
        st.session_state.execution_result = None
        st.session_state.start_time = None
        st.session_state.estimated_duration = None
    
    current_state = st.session_state.execution_state
    
    if current_state == "not_started":
        render_ready_to_start()
    elif current_state == "running":
        render_execution_progress()
    elif current_state == "completed":
        render_completion_success()
    elif current_state == "error":
        render_execution_error()


def render_no_request_state():
    """Show state when no discovery request is configured."""
    st.markdown('<div class="modern-container" style="padding-top: var(--space-16);">', unsafe_allow_html=True)
    
    ModernComponents.empty_state(
        title="No Discovery Configured",
        description="You need to configure your discovery settings first. Let's get you set up with the perfect search parameters.",
        action_text="Configure Discovery",
        action_key="configure_discovery"
    )
    
    if st.session_state.get("configure_discovery", False):
        ModernNavigation.navigate_to("setup")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_ready_to_start():
    """Show ready-to-start state with final confirmation."""
    st.markdown('<div class="modern-container"><div class="step-container">', unsafe_allow_html=True)
    
    # Get the discovery request details
    request = st.session_state.discovery_request
    
    ModernComponents.step_header(
        step_number=1,
        total_steps=1,
        title="Ready to Start Discovery",
        description="We're about to begin finding your ideal customers. This usually takes 10-20 minutes."
    )
    
    # Quick summary of what will happen
    segment_names = {
        "healthcare": "Healthcare EHR & Training",
        "corporate": "Corporate Learning Academies", 
        "providers": "Professional Training Providers"
    }
    
    segment_name = segment_names.get(request.segment.value, request.segment.value)
    
    ModernComponents.modern_card(f"""
    <div style="text-align: center;">
        <h3 style="color: var(--gray-900); margin-bottom: var(--space-4);">Discovery Summary</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--space-6);">
            <div>
                <div style="font-size: var(--font-size-lg); font-weight: 500; color: var(--primary); margin-bottom: var(--space-2);">{segment_name}</div>
                <div style="color: var(--gray-600); font-size: var(--font-size-sm);">Target Segment</div>
            </div>
            <div>
                <div style="font-size: var(--font-size-lg); font-weight: 500; color: var(--primary); margin-bottom: var(--space-2);">{request.targetcount}</div>
                <div style="color: var(--gray-600); font-size: var(--font-size-sm);">Organizations</div>
            </div>
            <div>
                <div style="font-size: var(--font-size-lg); font-weight: 500; color: var(--primary); margin-bottom: var(--space-2);">{request.region.value.upper()}</div>
                <div style="color: var(--gray-600); font-size: var(--font-size-sm);">Region</div>
            </div>
        </div>
    </div>
    """)
    
    # Estimated time based on parameters
    base_time = 8 if request.mode.value == "fast" else 15
    time_multiplier = request.targetcount / 15.0
    estimated_minutes = int(base_time * time_multiplier)
    
    st.markdown(f"""
    <div style="text-align: center; margin: var(--space-8) 0;">
        <p style="color: var(--gray-600); font-size: var(--font-size-base);">
            ⏱️ Estimated completion time: <strong>{estimated_minutes}-{estimated_minutes + 5} minutes</strong>
        </p>
        <p style="color: var(--gray-500); font-size: var(--font-size-sm); margin-top: var(--space-2);">
            You can close this window and come back - progress will be saved.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Large start button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Begin Discovery", key="begin_discovery", help="Start the discovery process"):
            start_discovery_execution()
    
    # Back button
    if st.button("← Change Settings", key="change_settings", help="Go back to modify your settings"):
        ModernNavigation.navigate_to("setup")
    
    st.markdown('</div></div>', unsafe_allow_html=True)


def render_execution_progress():
    """Show live progress during execution."""
    st.markdown('<div class="modern-container"><div class="step-container">', unsafe_allow_html=True)
    
    # Calculate progress and time estimates
    start_time = st.session_state.get("start_time")
    if start_time:
        elapsed_minutes = (time.time() - start_time) / 60
        estimated_total = st.session_state.get("estimated_duration", 15)
        remaining_minutes = max(0, estimated_total - elapsed_minutes)
        
        time_display = f"{int(remaining_minutes)} minutes remaining" if remaining_minutes > 1 else "Almost done!"
    else:
        time_display = "Starting up..."
    
    # Current step and completed steps
    current_step = st.session_state.get("current_step", "Initializing discovery...")
    completed_steps = st.session_state.get("completed_steps", [])
    
    # Progress display
    ModernComponents.progress_display(
        current_step=current_step,
        steps_completed=completed_steps,
        estimated_time=time_display
    )
    
    # Auto-refresh every 3 seconds to check for updates
    time.sleep(3)
    check_execution_status()
    
    # Cancel button (small, secondary)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Cancel", key="cancel_discovery", help="Stop the discovery process"):
            st.session_state.execution_state = "cancelled"
            st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)


def render_completion_success():
    """Show success state with results summary."""
    st.markdown('<div class="modern-container"><div class="step-container">', unsafe_allow_html=True)
    
    result = st.session_state.get("execution_result", {})
    
    # Success header
    st.markdown("""
    <div style="text-align: center; margin-bottom: var(--space-8);">
        <div style="font-size: var(--font-size-5xl); margin-bottom: var(--space-4);">🎉</div>
        <h2 style="color: var(--gray-900); margin-bottom: var(--space-2);">Discovery Complete!</h2>
        <p style="color: var(--gray-600);">We found some great prospects for you.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Results summary
    outputs = result.get("outputs", [])
    total_found = len(outputs)
    high_quality = len([o for o in outputs if o.get("tier") == "Confirmed"])
    
    ModernComponents.results_summary(
        title="Your Results",
        total_found=total_found,
        high_quality=high_quality,
        segments={"confirmed": high_quality, "probable": total_found - high_quality}
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 View Results", key="view_results", help="See detailed results"):
            st.session_state.discovery_result = result
            ModernNavigation.navigate_to("results")
    
    with col2:
        if st.button("🔄 New Discovery", key="new_discovery", help="Start another discovery"):
            # Clear execution state
            for key in ["execution_state", "current_step", "completed_steps", "execution_result", "start_time", "discovery_request"]:
                if key in st.session_state:
                    del st.session_state[key]
            ModernNavigation.navigate_to("setup")
    
    st.markdown('</div></div>', unsafe_allow_html=True)


def render_execution_error():
    """Show error state with retry options."""
    st.markdown('<div class="modern-container"><div class="step-container">', unsafe_allow_html=True)
    
    # Error header
    st.markdown("""
    <div style="text-align: center; margin-bottom: var(--space-8);">
        <div style="font-size: var(--font-size-5xl); margin-bottom: var(--space-4);">⚠️</div>
        <h2 style="color: var(--error); margin-bottom: var(--space-2);">Discovery Interrupted</h2>
        <p style="color: var(--gray-600);">Something went wrong during the discovery process.</p>
    </div>
    """, unsafe_allow_html=True)
    
    error_message = st.session_state.get("execution_error", "Unknown error occurred")
    
    ModernComponents.status_message(
        message=f"Error details: {error_message}",
        status_type="error"
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Try Again", key="retry_discovery", help="Retry the discovery"):
            # Reset execution state and retry
            st.session_state.execution_state = "not_started"
            st.session_state.current_step = None
            st.session_state.completed_steps = []
            st.rerun()
    
    with col2:
        if st.button("← Change Settings", key="back_to_setup", help="Modify settings and try again"):
            ModernNavigation.navigate_to("setup")
    
    st.markdown('</div></div>', unsafe_allow_html=True)


def start_discovery_execution():
    """Start the actual discovery execution."""
    st.session_state.execution_state = "running"
    st.session_state.start_time = time.time()
    st.session_state.current_step = "Starting discovery engines..."
    st.session_state.completed_steps = []
    
    # Estimate duration based on parameters
    request = st.session_state.discovery_request
    base_time = 8 if request.mode.value == "fast" else 15
    time_multiplier = request.targetcount / 15.0
    st.session_state.estimated_duration = int(base_time * time_multiplier)
    
    # Start the actual API call in background (mock for now)
    execute_discovery_api_call()
    
    st.rerun()


def execute_discovery_api_call():
    """Execute the actual API call to start discovery."""
    try:
        request = st.session_state.discovery_request
        
        # Convert to API format
        payload = {
            "segment": request.segment.value,
            "targetcount": request.targetcount,
            "region": request.region.value if request.region.value != "global" else "both",
            "mode": request.mode.value
        }
        
        # Make API call to localhost:8080/run
        response = requests.post("http://localhost:8080/run", json=payload, timeout=1800)
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.execution_result = result
            st.session_state.execution_state = "completed"
        else:
            st.session_state.execution_error = f"API returned status {response.status_code}: {response.text}"
            st.session_state.execution_state = "error"
            
    except requests.exceptions.RequestException as e:
        st.session_state.execution_error = f"Connection error: {str(e)}"
        st.session_state.execution_state = "error"
    except Exception as e:
        st.session_state.execution_error = f"Unexpected error: {str(e)}"
        st.session_state.execution_state = "error"


def check_execution_status():
    """Check the current execution status and update progress."""
    # Mock progress updates for demo purposes
    current_step = st.session_state.get("current_step")
    completed_steps = st.session_state.get("completed_steps", [])
    
    # Simulate progress steps
    progress_steps = [
        "Initializing search engines",
        "Discovering potential organizations", 
        "Extracting detailed information",
        "Scoring and ranking prospects",
        "Removing duplicates",
        "Enriching with company data",
        "Finalizing results"
    ]
    
    if len(completed_steps) < len(progress_steps) - 1:
        # Move to next step
        next_step_index = len(completed_steps)
        if next_step_index < len(progress_steps):
            if current_step and current_step != progress_steps[next_step_index]:
                completed_steps.append(current_step)
            st.session_state.current_step = progress_steps[next_step_index]
            st.session_state.completed_steps = completed_steps
    
    # Check if we should complete (mock timing)
    if st.session_state.get("start_time"):
        elapsed = time.time() - st.session_state.start_time
        # For demo, complete after 30 seconds
        if elapsed > 30:
            # Mock result
            st.session_state.execution_result = {
                "segment": st.session_state.discovery_request.segment.value,
                "count": 12,
                "outputs": [
                    {"organization": "Sample Health System", "tier": "Confirmed", "score": 95},
                    {"organization": "Regional Medical Center", "tier": "Confirmed", "score": 92},
                    {"organization": "Community Healthcare", "tier": "Probable", "score": 78}
                ]
            }
            st.session_state.execution_state = "completed"
    
    st.rerun()