"""
Modern, minimal UI components for ICP Discovery Engine.
Focus: Clean, spacious, single-purpose design with clear hierarchy.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from pathlib import Path


class ModernComponents:
    """Collection of modern, minimal UI components."""
    
    @staticmethod
    def load_modern_css():
        """Load the modern minimal stylesheet."""
        try:
            css_path = Path(__file__).parent.parent / "assets" / "modern_styles.css"
            if css_path.exists():
                with open(css_path, "r") as f:
                    css_content = f.read()
                st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            else:
                st.warning("Modern stylesheet not found.")
        except Exception as e:
            st.warning(f"Could not load modern stylesheet: {e}")
    
    @staticmethod
    def hero_section(title: str, subtitle: str, cta_text: str = "Get Started", cta_key: str = "hero_cta") -> bool:
        """Render a modern hero section with clear value proposition."""
        st.markdown(f"""
        <div class="hero-section">
            <div class="modern-container">
                <h1 class="hero-title">{title}</h1>
                <p class="hero-subtitle">{subtitle}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the CTA button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            return st.button(cta_text, key=cta_key, help="Start your discovery workflow")
    
    @staticmethod
    def feature_grid(features: List[Dict[str, str]]):
        """Render a clean grid of features."""
        cols = st.columns(len(features))
        
        for i, feature in enumerate(features):
            with cols[i]:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="feature-icon">{feature.get('icon', '🎯')}</div>
                    <h3 style="font-size: var(--font-size-lg); font-weight: 500; color: var(--gray-900); margin-bottom: var(--space-2);">
                        {feature.get('title', '')}
                    </h3>
                    <p style="color: var(--gray-600); font-size: var(--font-size-sm); line-height: 1.5;">
                        {feature.get('description', '')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def step_header(step_number: int, total_steps: int, title: str, description: str):
        """Render a step header with progress indication."""
        progress = step_number / total_steps
        
        st.markdown(f"""
        <div class="modern-container">
            <div class="step-container">
                <!-- Progress bar -->
                <div style="margin-bottom: var(--space-8);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
                        <span style="font-size: var(--font-size-sm); color: var(--gray-500);">
                            Step {step_number} of {total_steps}
                        </span>
                        <span style="font-size: var(--font-size-sm); color: var(--gray-500);">
                            {int(progress * 100)}% Complete
                        </span>
                    </div>
                    <div style="width: 100%; height: 4px; background-color: var(--gray-200); border-radius: 2px;">
                        <div style="width: {progress * 100}%; height: 100%; background-color: var(--primary); border-radius: 2px; transition: width 0.3s ease;"></div>
                    </div>
                </div>
                
                <!-- Step content -->
                <h2 class="step-title">{title}</h2>
                <p class="step-description">{description}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def modern_card(content: str, title: Optional[str] = None, padding: bool = True) -> None:
        """Render a modern card with clean styling."""
        card_class = "modern-card" if padding else "modern-card" 
        
        card_html = f"""
        <div class="{card_class}">
            {f'<h3 style="margin-bottom: var(--space-4); color: var(--gray-900); font-weight: 500;">{title}</h3>' if title else ''}
            {content}
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
    
    @staticmethod
    def simple_form(fields: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a clean, simple form with modern styling."""
        results = {}
        
        for field_name, config in fields.items():
            field_type = config.get("type", "text")
            label = config.get("label", field_name.title())
            help_text = config.get("help", "")
            
            if field_type == "select":
                results[field_name] = st.selectbox(
                    label,
                    options=config.get("options", []),
                    index=config.get("index", 0),
                    help=help_text,
                    key=f"form_{field_name}"
                )
            elif field_type == "number":
                results[field_name] = st.number_input(
                    label,
                    min_value=config.get("min_value", 0),
                    max_value=config.get("max_value", 100),
                    value=config.get("value", 10),
                    help=help_text,
                    key=f"form_{field_name}"
                )
            elif field_type == "slider":
                results[field_name] = st.slider(
                    label,
                    min_value=config.get("min_value", 0),
                    max_value=config.get("max_value", 100),
                    value=config.get("value", 10),
                    help=help_text,
                    key=f"form_{field_name}"
                )
        
        return results
    
    @staticmethod
    def progress_display(
        current_step: str,
        steps_completed: List[str],
        estimated_time: Optional[str] = None
    ):
        """Display elegant progress with current status."""
        st.markdown(f"""
        <div class="progress-container">
            <div style="text-align: center; margin-bottom: var(--space-6);">
                <h3 style="color: var(--gray-900); margin-bottom: var(--space-2);">{current_step}</h3>
                {f'<p style="color: var(--gray-600); font-size: var(--font-size-sm);">Estimated time remaining: {estimated_time}</p>' if estimated_time else ''}
            </div>
            
            <div style="margin-bottom: var(--space-4);">
                <div style="text-align: center; margin-bottom: var(--space-2);">
                    <div style="display: inline-block; width: 60px; height: 60px; border: 3px solid var(--primary); border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                </div>
            </div>
            
            <div style="text-align: center;">
                <p style="color: var(--gray-500); font-size: var(--font-size-sm); margin-bottom: var(--space-2);">Completed:</p>
                {''.join([f'<span class="status-badge status-success">✓ {step}</span>' for step in steps_completed])}
            </div>
        </div>
        
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def results_summary(
        title: str,
        total_found: int,
        high_quality: int,
        segments: Dict[str, int]
    ):
        """Display clean results summary."""
        st.markdown(f"""
        <div class="modern-card">
            <h2 style="color: var(--gray-900); margin-bottom: var(--space-6); text-align: center;">{title}</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--space-6); margin-bottom: var(--space-8);">
                <div style="text-align: center;">
                    <div style="font-size: var(--font-size-3xl); font-weight: 600; color: var(--primary); margin-bottom: var(--space-2);">
                        {total_found}
                    </div>
                    <div style="color: var(--gray-600); font-size: var(--font-size-sm);">Total Found</div>
                </div>
                
                <div style="text-align: center;">
                    <div style="font-size: var(--font-size-3xl); font-weight: 600; color: var(--success); margin-bottom: var(--space-2);">
                        {high_quality}
                    </div>
                    <div style="color: var(--gray-600); font-size: var(--font-size-sm);">High Quality</div>
                </div>
                
                <div style="text-align: center;">
                    <div style="font-size: var(--font-size-3xl); font-weight: 600; color: var(--primary); margin-bottom: var(--space-2);">
                        {int((high_quality / total_found) * 100) if total_found > 0 else 0}%
                    </div>
                    <div style="color: var(--gray-600); font-size: var(--font-size-sm);">Success Rate</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def navigation_buttons(
        back_text: Optional[str] = None,
        next_text: Optional[str] = None,
        back_key: str = "nav_back",
        next_key: str = "nav_next"
    ) -> Dict[str, bool]:
        """Render navigation buttons with modern styling."""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        results = {"back": False, "next": False}
        
        with col1:
            if back_text:
                results["back"] = st.button(back_text, key=back_key, help="Go back to previous step")
        
        with col3:
            if next_text:
                results["next"] = st.button(next_text, key=next_key, help="Continue to next step")
        
        return results
    
    @staticmethod
    def status_message(message: str, status_type: str = "info"):
        """Display a clean status message."""
        status_colors = {
            "success": "var(--success)",
            "warning": "var(--warning)", 
            "error": "var(--error)",
            "info": "var(--primary)"
        }
        
        icons = {
            "success": "✓",
            "warning": "⚠",
            "error": "✗", 
            "info": "ℹ"
        }
        
        color = status_colors.get(status_type, status_colors["info"])
        icon = icons.get(status_type, icons["info"])
        
        st.markdown(f"""
        <div style="
            background: rgba(71, 57, 231, 0.05);
            border-left: 4px solid {color};
            padding: var(--space-4);
            border-radius: var(--border-radius);
            margin: var(--space-4) 0;
        ">
            <div style="display: flex; align-items: center;">
                <span style="color: {color}; margin-right: var(--space-2); font-weight: 600;">{icon}</span>
                <span style="color: var(--gray-700);">{message}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def empty_state(title: str, description: str, action_text: str, action_key: str) -> bool:
        """Render a clean empty state with call to action."""
        st.markdown(f"""
        <div style="text-align: center; padding: var(--space-16) var(--space-4);">
            <div style="font-size: var(--font-size-5xl); margin-bottom: var(--space-4); opacity: 0.3;">📭</div>
            <h3 style="color: var(--gray-900); margin-bottom: var(--space-2);">{title}</h3>
            <p style="color: var(--gray-600); margin-bottom: var(--space-8); max-width: 400px; margin-left: auto; margin-right: auto;">
                {description}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Centered action button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            return st.button(action_text, key=action_key)


class ModernNavigation:
    """Modern navigation system with URL-style routing."""
    
    @staticmethod
    def init_navigation():
        """Initialize navigation state."""
        if "current_screen" not in st.session_state:
            st.session_state.current_screen = "home"
        if "nav_history" not in st.session_state:
            st.session_state.nav_history = ["home"]
    
    @staticmethod
    def navigate_to(screen: str):
        """Navigate to a specific screen."""
        st.session_state.current_screen = screen
        if screen not in st.session_state.nav_history:
            st.session_state.nav_history.append(screen)
        st.rerun()
    
    @staticmethod
    def go_back():
        """Navigate back to previous screen."""
        if len(st.session_state.nav_history) > 1:
            st.session_state.nav_history.pop()
            st.session_state.current_screen = st.session_state.nav_history[-1]
            st.rerun()
    
    @staticmethod
    def get_current_screen() -> str:
        """Get the current screen name."""
        return st.session_state.get("current_screen", "home")
    
    @staticmethod
    def breadcrumb(screens: Dict[str, str]):
        """Render breadcrumb navigation."""
        current = st.session_state.get("current_screen", "home")
        
        breadcrumb_items = []
        for i, screen in enumerate(st.session_state.get("nav_history", ["home"])):
            screen_name = screens.get(screen, screen.title())
            if screen == current:
                breadcrumb_items.append(f'<span style="color: var(--primary);">{screen_name}</span>')
            else:
                breadcrumb_items.append(f'<span style="color: var(--gray-500);">{screen_name}</span>')
        
        breadcrumb_html = ' → '.join(breadcrumb_items)
        
        st.markdown(f"""
        <div style="margin-bottom: var(--space-6); padding: var(--space-4) 0;">
            <div class="modern-container">
                <p style="font-size: var(--font-size-sm); color: var(--gray-600);">
                    {breadcrumb_html}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)