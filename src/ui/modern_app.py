"""
Modern ICP Discovery Engine UI Application
Clean, minimal interface with progressive disclosure and single-purpose screens.
"""

import streamlit as st
import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from components.modern_components import ModernComponents, ModernNavigation
from screens.home import render_home_screen
from screens.setup import render_setup_screen  
from screens.progress import render_progress_screen
from screens.results import render_results_screen


def main():
    """Main application entry point with modern routing."""
    
    # Page configuration
    st.set_page_config(
        page_title="ICP Discovery Engine",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Load modern styles
    ModernComponents.load_modern_css()
    
    # Initialize navigation
    ModernNavigation.init_navigation()
    
    # Get current screen
    current_screen = ModernNavigation.get_current_screen()
    
    # Render appropriate screen based on current navigation state
    if current_screen == "home":
        render_home_screen()
    elif current_screen == "setup":
        render_setup_screen()
    elif current_screen == "progress":
        render_progress_screen()
    elif current_screen == "results":
        render_results_screen()
    else:
        # Fallback to home if unknown screen
        st.session_state.current_screen = "home"
        st.rerun()


if __name__ == "__main__":
    main()