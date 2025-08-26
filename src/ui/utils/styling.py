"""
Styling utilities and helper functions for ICP Discovery Engine UI.
Provides CSS generation, theme management, and styling constants.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import json
from pathlib import Path


class StyleHelper:
    """Utility class for managing styles and CSS generation."""
    
    # Brand color constants
    BRAND_COLORS = {
        "primary_purple": "#4739E7",
        "background_pale": "#EDECFD", 
        "text_heading": "#0A1849",
        "text_body": "#0E0E1E",
        "light_purple": "#DAD7FA",
        "yellow_accent": "#FFBA00",
        "card_background": "#FFFFFF",
        "primary_purple_hover": "rgba(71, 57, 231, 0.6)",
        "light_purple_header": "#F6F6FE",
        "shadow_subtle": "0 0 4px rgba(0,0,0,0.08)"
    }
    
    # Typography constants
    TYPOGRAPHY = {
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "font_weights": {
            "light": 300,
            "regular": 400, 
            "medium": 500
        },
        "font_sizes": {
            "h1": "48px",
            "h2": "32px",
            "h3": "20px",
            "body": "16px",
            "small": "14px",
            "tiny": "12px"
        }
    }
    
    # Layout constants
    LAYOUT = {
        "baseline": "8px",
        "gutter": "20px",
        "outer_margin": "120px",
        "card_spacing": "20px",
        "min_button_height": "44px",
        "border_radius": "6px",
        "border_radius_tag": "12px",
        "circle_size": "28px"
    }
    
    @staticmethod
    def get_css_custom_properties() -> str:
        """Generate CSS custom properties from brand constants."""
        properties = []
        
        # Add color properties
        for key, value in StyleHelper.BRAND_COLORS.items():
            css_key = key.replace("_", "-")
            properties.append(f"    --{css_key}: {value};")
        
        # Add typography properties
        properties.append(f"    --font-family: {StyleHelper.TYPOGRAPHY['font_family']};")
        for weight_name, weight_value in StyleHelper.TYPOGRAPHY["font_weights"].items():
            css_key = weight_name.replace("_", "-")
            properties.append(f"    --font-weight-{css_key}: {weight_value};")
            
        # Add layout properties
        for key, value in StyleHelper.LAYOUT.items():
            css_key = key.replace("_", "-")
            properties.append(f"    --{css_key}: {value};")
        
        return ":root {\n" + "\n".join(properties) + "\n}"
    
    @staticmethod
    def generate_button_css(
        variant: str = "primary",
        size: str = "medium",
        custom_color: Optional[str] = None
    ) -> str:
        """Generate CSS for custom buttons."""
        base_styles = {
            "font-family": "var(--font-family)",
            "font-weight": "var(--font-weight-medium)",
            "border": "none",
            "border-radius": "var(--border-radius)",
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "text-decoration": "none",
            "display": "inline-flex",
            "align-items": "center",
            "justify-content": "center"
        }
        
        # Variant styles
        if variant == "primary":
            base_styles.update({
                "background-color": custom_color or "var(--primary-purple)",
                "color": "white",
                "box-shadow": "var(--shadow-subtle)"
            })
        elif variant == "secondary":
            base_styles.update({
                "background-color": "var(--card-background)",
                "color": custom_color or "var(--primary-purple)",
                "border": f"2px solid {custom_color or 'var(--primary-purple)'}",
            })
        elif variant == "ghost":
            base_styles.update({
                "background-color": "transparent",
                "color": custom_color or "var(--primary-purple)",
                "border": "1px solid transparent"
            })
        
        # Size styles
        size_configs = {
            "small": {"padding": "8px 16px", "font-size": "14px", "min-height": "32px"},
            "medium": {"padding": "12px 24px", "font-size": "16px", "min-height": "44px"},
            "large": {"padding": "16px 32px", "font-size": "18px", "min-height": "52px"}
        }
        
        if size in size_configs:
            base_styles.update(size_configs[size])
        
        # Convert to CSS string
        css_rules = []
        for prop, value in base_styles.items():
            css_rules.append(f"  {prop}: {value};")
        
        return "{\n" + "\n".join(css_rules) + "\n}"
    
    @staticmethod
    def generate_card_css(
        elevation: int = 1,
        padding: Optional[str] = None,
        background: Optional[str] = None
    ) -> str:
        """Generate CSS for brand-compliant cards."""
        shadow_levels = {
            0: "none",
            1: "var(--shadow-subtle)",
            2: "0 2px 8px rgba(0,0,0,0.12)",
            3: "0 4px 16px rgba(0,0,0,0.16)"
        }
        
        card_styles = {
            "background-color": background or "var(--card-background)",
            "border-radius": "var(--border-radius)",
            "box-shadow": shadow_levels.get(elevation, shadow_levels[1]),
            "padding": padding or "var(--card-spacing)",
            "border": "1px solid rgba(218, 215, 250, 0.3)"
        }
        
        css_rules = []
        for prop, value in card_styles.items():
            css_rules.append(f"  {prop}: {value};")
        
        return "{\n" + "\n".join(css_rules) + "\n}"
    
    @staticmethod
    def get_status_colors() -> Dict[str, str]:
        """Get color mapping for different status types."""
        return {
            "success": "#4bb543",
            "warning": "#FFBA00", 
            "error": "#ff4d4d",
            "info": "#4739E7",
            "neutral": "#888888"
        }
    
    @staticmethod
    def get_tier_colors() -> Dict[str, str]:
        """Get color mapping for quality tiers."""
        return {
            "confirmed": "#4bb543",
            "tier_1": "#4bb543",
            "probable": "#FFBA00",
            "tier_2": "#FFBA00",
            "possible": "#ff8c42", 
            "tier_3": "#ff8c42",
            "unlikely": "#ff4d4d"
        }
    
    @staticmethod
    def create_gradient(
        start_color: str,
        end_color: str,
        direction: str = "to right"
    ) -> str:
        """Create a CSS gradient string."""
        return f"linear-gradient({direction}, {start_color}, {end_color})"
    
    @staticmethod
    def inject_custom_css(css: str, key: Optional[str] = None) -> None:
        """Inject custom CSS into Streamlit app."""
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    @staticmethod
    def create_responsive_breakpoints() -> str:
        """Generate responsive CSS media queries."""
        return """
        /* Mobile */
        @media (max-width: 768px) {
            :root {
                --outer-margin: 20px;
                --card-spacing: 16px;
            }
            
            .main-container {
                padding: 0 20px;
            }
            
            .stTabs [data-baseweb="tab"] {
                padding: 12px 16px !important;
                font-size: 14px !important;
            }
        }
        
        /* Tablet */
        @media (max-width: 1024px) {
            :root {
                --outer-margin: 40px;
            }
            
            .main-container {
                padding: 0 40px;
            }
        }
        
        /* Large screens */
        @media (min-width: 1920px) {
            .main-container {
                max-width: 1920px;
                margin: 0 auto;
            }
        }
        """
    
    @staticmethod
    def create_focus_styles() -> str:
        """Generate accessibility-focused CSS styles."""
        return """
        /* Focus styles for accessibility */
        .stButton > button:focus,
        .stSelectbox > div > div:focus-within,
        .stTextInput > div > div:focus-within,
        .stNumberInput > div > div:focus-within {
            outline: 2px solid var(--primary-purple) !important;
            outline-offset: 2px !important;
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            :root {
                --shadow-subtle: 0 0 6px rgba(0,0,0,0.3);
            }
            
            .brand-card {
                border: 2px solid var(--light-purple);
            }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            .stButton > button {
                transition: none !important;
            }
            
            .stButton > button:hover {
                transform: none !important;
            }
        }
        """
    
    @staticmethod
    def create_loading_animation() -> str:
        """Generate CSS for loading animations."""
        return """
        .brand-spinner {
            border: 3px solid var(--light-purple);
            border-top: 3px solid var(--primary-purple);
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 8px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .brand-pulse {
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .brand-fade-in {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            0% { opacity: 0; }
            100% { opacity: 1; }
        }
        """


class ThemeManager:
    """Manages theme switching and customization."""
    
    def __init__(self):
        self.themes = {
            "default": StyleHelper.BRAND_COLORS,
            "dark": self._create_dark_theme(),
            "high_contrast": self._create_high_contrast_theme()
        }
    
    def _create_dark_theme(self) -> Dict[str, str]:
        """Create a dark theme variant."""
        return {
            "primary_purple": "#6C5CE7",
            "background_pale": "#2D2D2D",
            "text_heading": "#FFFFFF", 
            "text_body": "#E0E0E0",
            "light_purple": "#4A4A4A",
            "yellow_accent": "#FFD700",
            "card_background": "#3D3D3D",
            "primary_purple_hover": "rgba(108, 92, 231, 0.6)",
            "light_purple_header": "#404040",
            "shadow_subtle": "0 0 6px rgba(0,0,0,0.5)"
        }
    
    def _create_high_contrast_theme(self) -> Dict[str, str]:
        """Create a high contrast theme for accessibility."""
        return {
            "primary_purple": "#0000FF",
            "background_pale": "#FFFFFF",
            "text_heading": "#000000",
            "text_body": "#000000", 
            "light_purple": "#E0E0E0",
            "yellow_accent": "#FF0000",
            "card_background": "#FFFFFF",
            "primary_purple_hover": "#000080",
            "light_purple_header": "#F0F0F0",
            "shadow_subtle": "0 0 8px rgba(0,0,0,0.8)"
        }
    
    def get_theme_css(self, theme_name: str = "default") -> str:
        """Get complete CSS for a specific theme."""
        if theme_name not in self.themes:
            theme_name = "default"
        
        theme_colors = self.themes[theme_name]
        
        # Generate CSS custom properties for the theme
        properties = []
        for key, value in theme_colors.items():
            css_key = key.replace("_", "-")
            properties.append(f"    --{css_key}: {value};")
        
        return ":root {\n" + "\n".join(properties) + "\n}"
    
    def apply_theme(self, theme_name: str = "default") -> None:
        """Apply a theme to the current Streamlit app."""
        theme_css = self.get_theme_css(theme_name)
        StyleHelper.inject_custom_css(theme_css)


class ComponentStyler:
    """Helper class for styling specific UI components."""
    
    @staticmethod
    def style_dataframe(
        df_container_css: str = "",
        header_color: str = "var(--light-purple-header)",
        alternating_rows: bool = True
    ) -> None:
        """Apply styling to Streamlit dataframes."""
        css = f"""
        .stDataFrame {{
            {df_container_css}
            border-radius: var(--border-radius) !important;
            overflow: hidden !important;
            box-shadow: var(--shadow-subtle) !important;
        }}
        
        .stDataFrame thead th {{
            background-color: {header_color} !important;
            color: var(--text-heading) !important;
            font-family: var(--font-family) !important;
            font-weight: var(--font-weight-medium) !important;
            border-bottom: 2px solid var(--primary-purple) !important;
        }}
        """
        
        if alternating_rows:
            css += """
            .stDataFrame tbody tr:nth-child(even) {
                background-color: rgba(237, 236, 253, 0.3) !important;
            }
            
            .stDataFrame tbody tr:hover {
                background-color: var(--light-purple) !important;
            }
            """
        
        StyleHelper.inject_custom_css(css)
    
    @staticmethod
    def style_metrics(custom_colors: Optional[Dict[str, str]] = None) -> None:
        """Apply brand styling to Streamlit metrics."""
        css = """
        .stMetric {
            background-color: var(--card-background) !important;
            border-radius: var(--border-radius) !important;
            box-shadow: var(--shadow-subtle) !important;
            padding: 16px !important;
            border: 1px solid rgba(218, 215, 250, 0.3) !important;
        }
        
        .stMetric [data-testid="metric-label"] {
            font-family: var(--font-family) !important;
            font-weight: var(--font-weight-medium) !important;
            color: var(--text-heading) !important;
            font-size: 14px !important;
        }
        
        .stMetric [data-testid="metric-value"] {
            font-family: var(--font-family) !important;
            font-weight: var(--font-weight-medium) !important;
            color: var(--primary-purple) !important;
            font-size: 24px !important;
        }
        """
        
        StyleHelper.inject_custom_css(css)
    
    @staticmethod
    def style_sidebar() -> None:
        """Apply brand styling to Streamlit sidebar."""
        css = """
        .css-1d391kg {
            background-color: var(--card-background) !important;
            border-right: 1px solid var(--light-purple) !important;
        }
        
        .css-1d391kg .stButton > button {
            width: 100% !important;
            margin-bottom: 8px !important;
        }
        """
        
        StyleHelper.inject_custom_css(css)


def load_brand_system() -> None:
    """Load the complete brand system CSS."""
    try:
        # Load main stylesheet
        css_path = Path(__file__).parent.parent / "assets" / "styles.css"
        if css_path.exists():
            with open(css_path, "r") as f:
                css_content = f.read()
            StyleHelper.inject_custom_css(css_content)
        
        # Add responsive breakpoints
        StyleHelper.inject_custom_css(StyleHelper.create_responsive_breakpoints())
        
        # Add accessibility styles
        StyleHelper.inject_custom_css(StyleHelper.create_focus_styles())
        
        # Add animations
        StyleHelper.inject_custom_css(StyleHelper.create_loading_animation())
        
    except Exception as e:
        st.warning(f"Could not load complete brand system: {e}")
        # Fallback to basic styling
        StyleHelper.inject_custom_css(StyleHelper.get_css_custom_properties())