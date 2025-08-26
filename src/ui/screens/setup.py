"""
Modern setup wizard for ICP Discovery Engine.
Simple 3-step configuration process with smart defaults.
"""

import streamlit as st
from components.modern_components import ModernComponents, ModernNavigation
from utils.api_client import Segment, Mode, Region, RunRequest


def render_setup_screen():
    """Render the modern setup wizard."""
    
    # Initialize setup state
    if "setup_step" not in st.session_state:
        st.session_state.setup_step = 1
    if "setup_data" not in st.session_state:
        st.session_state.setup_data = {}
    
    current_step = st.session_state.setup_step
    
    if current_step == 1:
        render_step_1_target()
    elif current_step == 2:
        render_step_2_scope()
    elif current_step == 3:
        render_step_3_confirm()


def render_step_1_target():
    """Step 1: Choose target segment with clear descriptions."""
    
    ModernComponents.step_header(
        step_number=1,
        total_steps=3,
        title="What type of organizations are you targeting?",
        description="Choose your ideal customer profile to get the most relevant results."
    )
    
    # Target segment selection with rich descriptions
    st.markdown('<div class="modern-container"><div class="step-container">', unsafe_allow_html=True)
    
    segments = [
        {
            "value": "healthcare",
            "title": "Healthcare EHR & Training",
            "description": "Provider organizations with active EHR systems and VILT training programs",
            "examples": "Hospitals, clinics, health systems implementing electronic health records",
            "icon": "🏥"
        },
        {
            "value": "corporate",
            "title": "Corporate Learning Academies", 
            "description": "Large enterprises (7,500+ employees) with named learning academies",
            "examples": "Fortune 1000 companies, global enterprises with structured training programs",
            "icon": "🏢"
        },
        {
            "value": "training",
            "title": "Professional Training Providers",
            "description": "B2B training companies offering live virtual instruction",
            "examples": "Training consultancies, education companies, certification providers",
            "icon": "🎓"
        }
    ]
    
    # Create selection cards
    selected_segment = None
    
    for segment in segments:
        # Create a card for each segment
        card_html = f"""
        <div style="
            border: 2px solid {'var(--primary)' if st.session_state.setup_data.get('segment') == segment['value'] else 'var(--gray-200)'};
            border-radius: var(--border-radius-lg);
            padding: var(--space-6);
            margin-bottom: var(--space-4);
            background: {'rgba(71, 57, 231, 0.02)' if st.session_state.setup_data.get('segment') == segment['value'] else 'var(--white)'};
            cursor: pointer;
            transition: var(--transition);
        " onclick="selectSegment('{segment['value']}')">
            <div style="display: flex; align-items: flex-start; gap: var(--space-4);">
                <div style="font-size: var(--font-size-2xl);">{segment['icon']}</div>
                <div style="flex: 1;">
                    <h3 style="color: var(--gray-900); margin-bottom: var(--space-2); font-size: var(--font-size-lg);">
                        {segment['title']}
                    </h3>
                    <p style="color: var(--gray-600); margin-bottom: var(--space-2); line-height: 1.4;">
                        {segment['description']}
                    </p>
                    <p style="color: var(--gray-500); font-size: var(--font-size-sm); font-style: italic;">
                        Examples: {segment['examples']}
                    </p>
                </div>
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Hidden button for selection
        if st.button("Select", key=f"select_{segment['value']}", help=f"Choose {segment['title']}"):
            st.session_state.setup_data['segment'] = segment['value']
            selected_segment = segment['value']
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Navigation buttons
    nav_result = ModernComponents.navigation_buttons(
        back_text="← Back",
        next_text="Continue →",
        back_key="step1_back",
        next_key="step1_next"
    )
    
    if nav_result["back"]:
        ModernNavigation.navigate_to("home")
    
    if nav_result["next"] and st.session_state.setup_data.get('segment'):
        st.session_state.setup_step = 2
        st.rerun()
    elif nav_result["next"]:
        ModernComponents.status_message("Please select a target segment to continue.", "warning")


def render_step_2_scope():
    """Step 2: Configure scope and preferences."""
    
    ModernComponents.step_header(
        step_number=2,
        total_steps=3,
        title="Configure your search scope",
        description="Set the size and focus of your discovery to match your capacity."
    )
    
    st.markdown('<div class="modern-container"><div class="step-container">', unsafe_allow_html=True)
    
    # Simple form with smart defaults
    col1, col2 = st.columns(2)
    
    with col1:
        # Target count with smart suggestions
        segment = st.session_state.setup_data.get('segment', 'healthcare')
        default_counts = {
            'healthcare': 15,
            'corporate': 10,
            'training': 20
        }
        
        target_count = st.number_input(
            "How many organizations to find?",
            min_value=5,
            max_value=50,
            value=default_counts.get(segment, 15),
            step=5,
            help="Start with a smaller number for faster results. You can always run again for more.",
            key="target_count"
        )
        st.session_state.setup_data['target_count'] = target_count
        
        # Simple explanation of what this means
        if target_count <= 10:
            effort_desc = "Quick search (5-10 minutes)"
        elif target_count <= 25:
            effort_desc = "Standard search (10-20 minutes)" 
        else:
            effort_desc = "Comprehensive search (20+ minutes)"
            
        st.markdown(f"""
        <p style="color: var(--gray-600); font-size: var(--font-size-sm); margin-top: var(--space-2);">
            ⏱️ {effort_desc}
        </p>
        """, unsafe_allow_html=True)
    
    with col2:
        # Geographic focus
        region_options = {
            "North America": "na",
            "Europe/Middle East": "emea", 
            "Global (slower)": "global"
        }
        
        region_choice = st.selectbox(
            "Geographic focus?",
            options=list(region_options.keys()),
            index=0,
            help="Regional searches are faster and more targeted.",
            key="region_choice"
        )
        st.session_state.setup_data['region'] = region_options[region_choice]
        
        # Quality vs speed preference
        mode_choice = st.radio(
            "Search approach?",
            options=["Fast & Focused", "Deep & Thorough"],
            index=0,
            help="Fast gives good results quickly. Deep takes longer but finds more details.",
            key="mode_choice"
        )
        st.session_state.setup_data['mode'] = 'fast' if 'Fast' in mode_choice else 'deep'
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Navigation buttons
    nav_result = ModernComponents.navigation_buttons(
        back_text="← Back",
        next_text="Review →",
        back_key="step2_back", 
        next_key="step2_next"
    )
    
    if nav_result["back"]:
        st.session_state.setup_step = 1
        st.rerun()
        
    if nav_result["next"]:
        st.session_state.setup_step = 3
        st.rerun()


def render_step_3_confirm():
    """Step 3: Confirm and start."""
    
    ModernComponents.step_header(
        step_number=3,
        total_steps=3,
        title="Ready to start your discovery?",
        description="Review your settings and we'll find your ideal customers."
    )
    
    st.markdown('<div class="modern-container"><div class="step-container">', unsafe_allow_html=True)
    
    # Clean summary of selections
    setup_data = st.session_state.setup_data
    
    segment_names = {
        'healthcare': 'Healthcare EHR & Training',
        'corporate': 'Corporate Learning Academies',
        'training': 'Professional Training Providers'
    }
    
    region_names = {
        'na': 'North America',
        'emea': 'Europe/Middle East',
        'global': 'Global'
    }
    
    mode_names = {
        'fast': 'Fast & Focused',
        'deep': 'Deep & Thorough'
    }
    
    ModernComponents.modern_card(f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-6);">
        <div>
            <h4 style="color: var(--gray-700); margin-bottom: var(--space-2); font-size: var(--font-size-base);">Target</h4>
            <p style="color: var(--gray-900); font-weight: 500;">{segment_names.get(setup_data.get('segment', ''), 'Not selected')}</p>
        </div>
        <div>
            <h4 style="color: var(--gray-700); margin-bottom: var(--space-2); font-size: var(--font-size-base);">Quantity</h4>
            <p style="color: var(--gray-900); font-weight: 500;">{setup_data.get('target_count', 0)} organizations</p>
        </div>
        <div>
            <h4 style="color: var(--gray-700); margin-bottom: var(--space-2); font-size: var(--font-size-base);">Region</h4>
            <p style="color: var(--gray-900); font-weight: 500;">{region_names.get(setup_data.get('region', ''), 'Not selected')}</p>
        </div>
        <div>
            <h4 style="color: var(--gray-700); margin-bottom: var(--space-2); font-size: var(--font-size-base);">Approach</h4>
            <p style="color: var(--gray-900); font-weight: 500;">{mode_names.get(setup_data.get('mode', ''), 'Not selected')}</p>
        </div>
    </div>
    """, title="Your Discovery Settings")
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Final CTA
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Discovery", key="start_discovery_final", help="Begin finding your ideal customers"):
            # Store the final configuration
            st.session_state.discovery_request = create_run_request(setup_data)
            ModernNavigation.navigate_to("progress")
    
    # Navigation buttons
    nav_result = ModernComponents.navigation_buttons(
        back_text="← Back",
        next_text=None,
        back_key="step3_back"
    )
    
    if nav_result["back"]:
        st.session_state.setup_step = 2
        st.rerun()


def create_run_request(setup_data: dict) -> RunRequest:
    """Create a RunRequest from setup data."""
    segment_map = {
        'healthcare': Segment.HEALTHCARE,
        'corporate': Segment.CORPORATE, 
        'training': Segment.PROVIDERS
    }
    
    region_map = {
        'na': Region.NA,
        'emea': Region.EMEA,
        'global': Region.BOTH
    }
    
    mode_map = {
        'fast': Mode.FAST,
        'deep': Mode.DEEP
    }
    
    return RunRequest(
        segment=segment_map.get(setup_data.get('segment'), Segment.HEALTHCARE),
        targetcount=setup_data.get('target_count', 10),
        region=region_map.get(setup_data.get('region'), Region.NA),
        mode=mode_map.get(setup_data.get('mode'), Mode.FAST)
    )