"""
Modern home screen for ICP Discovery Engine.
Clean, focused welcome experience with clear value proposition.
"""

import streamlit as st
from components.modern_components import ModernComponents, ModernNavigation


def render_home_screen():
    """Render the modern home screen with clear value proposition."""
    
    # Hero section with clear value proposition
    if ModernComponents.hero_section(
        title="Find Your Ideal Customers",
        subtitle="Discover high-quality prospects across Healthcare, Corporate, and Training sectors with AI-powered intelligence.",
        cta_text="Start Discovery",
        cta_key="start_discovery"
    ):
        ModernNavigation.navigate_to("setup")
    
    # Feature showcase
    st.markdown('<div class="content-section"><div class="modern-container">', unsafe_allow_html=True)
    
    features = [
        {
            "icon": "🎯",
            "title": "Targeted Discovery",
            "description": "Find organizations that match your ideal customer profile with precision AI targeting."
        },
        {
            "icon": "⚡",
            "title": "Fast Results", 
            "description": "Get qualified leads in minutes, not hours. Smart automation handles the heavy lifting."
        },
        {
            "icon": "📊",
            "title": "Quality Insights",
            "description": "Rich data and scoring to help you prioritize the best prospects for outreach."
        }
    ]
    
    ModernComponents.feature_grid(features)
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Simple stats or social proof section
    st.markdown("""
    <div style="text-align: center; padding: var(--space-16) 0; background: var(--white);">
        <div class="modern-container">
            <p style="color: var(--gray-600); font-size: var(--font-size-lg); margin-bottom: var(--space-8);">
                Trusted by teams to find quality prospects
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-8);">
                <div style="text-align: center;">
                    <div style="font-size: var(--font-size-2xl); font-weight: 600; color: var(--primary);">Healthcare</div>
                    <p style="color: var(--gray-600); font-size: var(--font-size-sm);">EHR & Training Organizations</p>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: var(--font-size-2xl); font-weight: 600; color: var(--primary);">Corporate</div>
                    <p style="color: var(--gray-600); font-size: var(--font-size-sm);">Enterprise Learning Academies</p>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: var(--font-size-2xl); font-weight: 600; color: var(--primary);">Training</div>
                    <p style="color: var(--gray-600); font-size: var(--font-size-sm);">Professional Training Providers</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Simple footer
    st.markdown("""
    <div style="text-align: center; padding: var(--space-8) 0; background: var(--gray-50); border-top: 1px solid var(--gray-200);">
        <p style="color: var(--gray-500); font-size: var(--font-size-sm);">
            ICP Discovery Engine • Powered by AI
        </p>
    </div>
    """, unsafe_allow_html=True)