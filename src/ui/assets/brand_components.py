"""
Reusable brand-compliant Streamlit components for ICP Discovery Engine.
Implements the brand design system with consistent styling and behavior.
"""

import streamlit as st
from typing import Optional, Dict, Any, List, Union
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


class BrandComponents:
    """Collection of brand-compliant UI components."""
    
    @staticmethod
    def load_brand_css():
        """Load the main brand stylesheet."""
        try:
            from pathlib import Path
            css_path = Path(__file__).parent / "styles.css"
            if css_path.exists():
                with open(css_path, "r") as f:
                    css_content = f.read()
                st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            else:
                st.warning("Brand stylesheet not found. Using fallback styling.")
                # Fallback basic CSS
                from ..utils.styling import StyleHelper
                StyleHelper.inject_custom_css(StyleHelper.get_css_custom_properties())
        except Exception as e:
            st.warning(f"Could not load brand stylesheet: {e}")
            # Use styling utilities as fallback
            try:
                from ..utils.styling import load_brand_system
                load_brand_system()
            except:
                pass
    
    @staticmethod
    def render_logo(size: int = 120) -> str:
        """
        Render the brand logo with geometric squares design.
        Returns SVG string for the logo.
        """
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
            <!-- Large central square in golden yellow -->
            <rect x="30" y="30" width="60" height="60" fill="#FFC107" stroke="#4739E7" stroke-width="2" rx="6"/>
            
            <!-- Top-left small square in purple -->
            <rect x="10" y="10" width="25" height="25" fill="#4739E7" rx="3"/>
            
            <!-- Top-right small square in purple -->
            <rect x="85" y="10" width="25" height="25" fill="#4739E7" rx="3"/>
            
            <!-- Bottom-right small square in purple -->
            <rect x="85" y="85" width="25" height="25" fill="#4739E7" rx="3"/>
            
            <!-- Optional text/initials -->
            <text x="60" y="70" text-anchor="middle" fill="#4739E7" font-family="Inter" font-weight="500" font-size="24">ICP</text>
        </svg>
        """
    
    @staticmethod
    def brand_card(title: str, content: str, header_color: str = "#F6F6FE") -> None:
        """Render a brand-compliant card with header and content."""
        st.markdown(f"""
        <div class="brand-card">
            <div class="brand-card-header" style="background-color: {header_color};">
                {title}
            </div>
            <div>
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def brand_button(
        label: str, 
        key: Optional[str] = None, 
        help: Optional[str] = None,
        variant: str = "primary",
        disabled: bool = False
    ) -> bool:
        """
        Render a brand-compliant button.
        variant: 'primary' or 'secondary'
        """
        css_class = "secondary-button" if variant == "secondary" else ""
        
        if css_class:
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        
        result = st.button(label, key=key, help=help, disabled=disabled)
        
        if css_class:
            st.markdown('</div>', unsafe_allow_html=True)
        
        return result
    
    @staticmethod
    def status_indicator(status: str, label: str = "") -> None:
        """Render a status indicator with brand colors."""
        status_class = f"status-{status.lower()}"
        icon_map = {
            "online": "🟢",
            "offline": "🔴", 
            "unknown": "🟡",
            "warning": "⚠️",
            "success": "✅",
            "error": "❌"
        }
        
        icon = icon_map.get(status.lower(), "⚪")
        display_text = f"{icon} {label}" if label else icon
        
        st.markdown(f'<span class="{status_class}">{display_text}</span>', unsafe_allow_html=True)
    
    @staticmethod
    def brand_metric_card(
        title: str, 
        value: Union[str, int, float], 
        delta: Optional[str] = None,
        help: Optional[str] = None
    ) -> None:
        """Render a metric card with brand styling."""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.metric(
                label=title,
                value=value,
                delta=delta,
                help=help
            )
    
    @staticmethod
    def brand_tag(text: str, color: str = "#4739E7") -> str:
        """Generate a brand-compliant tag."""
        return f'<span class="brand-tag" style="color: {color};">{text}</span>'
    
    @staticmethod
    def numbered_circle(number: Union[str, int], color: str = "#4739E7") -> str:
        """Generate a numbered circle with brand styling."""
        return f'<span class="brand-circle" style="background-color: {color};">{number}</span>'
    
    @staticmethod
    def highlight_callout(text: str) -> None:
        """Render a highlighted callout box."""
        st.markdown(f"""
        <div class="highlight-callout">
            {text}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def loading_spinner(text: str = "Loading...") -> None:
        """Render a brand-compliant loading spinner."""
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; padding: 20px;">
            <div class="brand-spinner"></div>
            <span style="margin-left: 8px; font-family: Inter; color: #0A1849;">{text}</span>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def brand_progress_bar(progress: float, text: str = "") -> None:
        """Render a progress bar with brand colors."""
        st.progress(progress, text)
    
    @staticmethod
    def get_brand_chart_colors() -> Dict[str, str]:
        """Get the standard brand colors for charts."""
        return {
            "primary": "#4739E7",
            "secondary": "#FFBA00", 
            "accent1": "#DAD7FA",
            "accent2": "rgba(71, 57, 231, 0.3)",
            "accent3": "rgba(255, 186, 0, 0.3)",
            "background": "#EDECFD",
            "text": "#0A1849"
        }
    
    @staticmethod
    def brand_plotly_theme() -> Dict[str, Any]:
        """Get Plotly theme configuration with brand colors."""
        colors = BrandComponents.get_brand_chart_colors()
        
        return {
            "layout": {
                "colorway": [colors["primary"], colors["secondary"], colors["accent1"]],
                "font": {"family": "Inter", "color": colors["text"]},
                "paper_bgcolor": colors["background"],
                "plot_bgcolor": "white",
                "title": {
                    "font": {"size": 20, "family": "Inter", "color": colors["text"]}
                },
                "xaxis": {
                    "gridcolor": colors["accent1"],
                    "tickfont": {"family": "Inter", "color": colors["text"]}
                },
                "yaxis": {
                    "gridcolor": colors["accent1"],
                    "tickfont": {"family": "Inter", "color": colors["text"]}
                }
            }
        }
    
    @staticmethod
    def tier_status_badge(tier: str) -> str:
        """Generate a status badge for tier information."""
        tier_colors = {
            "confirmed": "#4bb543",
            "tier 1": "#4bb543",
            "probable": "#FFBA00",
            "tier 2": "#FFBA00", 
            "possible": "#ff8c42",
            "tier 3": "#ff8c42",
            "unlikely": "#ff4d4d"
        }
        
        color = tier_colors.get(tier.lower(), "#888888")
        return f'<span class="brand-tag" style="background-color: {color}; color: white;">{tier.upper()}</span>'
    
    @staticmethod
    def quality_indicator(score: float) -> str:
        """Generate a quality indicator based on score."""
        if score >= 90:
            return BrandComponents.tier_status_badge("Confirmed")
        elif score >= 70:
            return BrandComponents.tier_status_badge("Probable") 
        elif score >= 50:
            return BrandComponents.tier_status_badge("Possible")
        else:
            return BrandComponents.tier_status_badge("Unlikely")
    
    @staticmethod
    def render_data_table(
        data: List[Dict[str, Any]], 
        columns: Optional[List[str]] = None,
        height: int = 400
    ) -> None:
        """Render a data table with brand styling."""
        if not data:
            st.info("No data available to display.")
            return
            
        import pandas as pd
        df = pd.DataFrame(data)
        
        if columns:
            df = df[columns] if all(col in df.columns for col in columns) else df
            
        st.dataframe(
            df,
            height=height,
            use_container_width=True
        )
    
    @staticmethod
    def section_header(title: str, description: str = "") -> None:
        """Render a section header with brand styling."""
        st.markdown(f"""
        <div style="margin-bottom: 24px;">
            <h2 style="color: #0A1849; font-weight: 300; margin-bottom: 8px;">{title}</h2>
            {f'<p style="color: #0E0E1E; margin-bottom: 0;">{description}</p>' if description else ''}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def dashboard_header(title: str, subtitle: str = "", logo_size: int = 60) -> None:
        """Render the main dashboard header with logo."""
        col1, col2, col3 = st.columns([1, 6, 1])
        
        with col1:
            st.markdown(BrandComponents.render_logo(logo_size), unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px 0;">
                <h1 style="margin-bottom: 8px; color: #0A1849;">{title}</h1>
                {f'<p style="font-size: 18px; color: #0E0E1E; margin: 0;">{subtitle}</p>' if subtitle else ''}
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Space for status indicators or quick actions
            pass
    
    @staticmethod
    def quick_stats_grid(stats: Dict[str, Union[str, int, float]]) -> None:
        """Render a grid of quick statistics."""
        num_stats = len(stats)
        cols = st.columns(num_stats)
        
        for i, (label, value) in enumerate(stats.items()):
            with cols[i]:
                BrandComponents.brand_metric_card(label, value)
    
    @staticmethod
    def render_workflow_summary(
        workflow_name: str,
        parameters: Dict[str, Any],
        results: Dict[str, Any],
        timestamp: datetime
    ) -> None:
        """Render a complete workflow summary with brand styling."""
        st.markdown(f"""
        <div class="brand-card">
            <div class="brand-card-header">
                {BrandComponents.numbered_circle("✓")} {workflow_name} Summary
            </div>
            <div style="padding: 16px 0;">
                <p><strong>Executed:</strong> {timestamp.strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p><strong>Parameters:</strong></p>
                <ul>
        """, unsafe_allow_html=True)
        
        for key, value in parameters.items():
            st.markdown(f"<li>{key}: {value}</li>", unsafe_allow_html=True)
            
        st.markdown(f"""
                </ul>
                <p><strong>Results:</strong></p>
                <ul>
        """, unsafe_allow_html=True)
        
        for key, value in results.items():
            st.markdown(f"<li>{key}: {value}</li>", unsafe_allow_html=True)
            
        st.markdown("</ul></div></div>", unsafe_allow_html=True)


class ChartHelper:
    """Helper class for creating brand-compliant charts."""
    
    @staticmethod
    def create_pie_chart(data: Dict[str, int], title: str) -> go.Figure:
        """Create a pie chart with brand colors."""
        colors = BrandComponents.get_brand_chart_colors()
        
        fig = go.Figure(data=[go.Pie(
            labels=list(data.keys()),
            values=list(data.values()),
            hole=0.4,
            marker=dict(
                colors=[colors["primary"], colors["secondary"], colors["accent1"]],
                line=dict(color="#FFFFFF", width=2)
            )
        )])
        
        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "font": {"size": 20, "family": "Inter", "color": colors["text"]}
            },
            font=dict(family="Inter", color=colors["text"]),
            paper_bgcolor=colors["background"],
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )
        
        return fig
    
    @staticmethod
    def create_bar_chart(data: Dict[str, Union[int, float]], title: str, x_label: str = "", y_label: str = "") -> go.Figure:
        """Create a bar chart with brand colors."""
        colors = BrandComponents.get_brand_chart_colors()
        
        fig = go.Figure(data=[go.Bar(
            x=list(data.keys()),
            y=list(data.values()),
            marker_color=colors["primary"],
            marker_line=dict(color=colors["text"], width=1)
        )])
        
        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "font": {"size": 20, "family": "Inter", "color": colors["text"]}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            font=dict(family="Inter", color=colors["text"]),
            paper_bgcolor=colors["background"],
            plot_bgcolor="white",
            xaxis=dict(gridcolor=colors["accent1"]),
            yaxis=dict(gridcolor=colors["accent1"])
        )
        
        return fig
    
    @staticmethod
    def create_histogram(values: List[Union[int, float]], title: str, x_label: str = "", y_label: str = "Count") -> go.Figure:
        """Create a histogram with brand colors."""
        colors = BrandComponents.get_brand_chart_colors()
        
        fig = go.Figure(data=[go.Histogram(
            x=values,
            marker_color=colors["primary"],
            opacity=0.8,
            marker_line=dict(color=colors["text"], width=1)
        )])
        
        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "font": {"size": 20, "family": "Inter", "color": colors["text"]}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            font=dict(family="Inter", color=colors["text"]),
            paper_bgcolor=colors["background"],
            plot_bgcolor="white",
            xaxis=dict(gridcolor=colors["accent1"]),
            yaxis=dict(gridcolor=colors["accent1"])
        )
        
        return fig


class FormHelper:
    """Helper class for creating brand-compliant forms."""
    
    @staticmethod
    def render_form_section(title: str, description: str = "") -> None:
        """Render a form section header."""
        st.markdown(f"""
        <div style="margin: 24px 0 16px 0;">
            <h3 style="color: #0A1849; margin-bottom: 4px;">{title}</h3>
            {f'<p style="color: #0E0E1E; font-size: 14px; margin: 0;">{description}</p>' if description else ''}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_parameter_form(
        parameters: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a dynamic form based on parameter definitions.
        
        parameters structure:
        {
            "param_name": {
                "type": "selectbox|number_input|text_input|checkbox",
                "label": "Display Label",
                "options": [...],  # for selectbox
                "min_value": 0,    # for number_input
                "max_value": 100,  # for number_input
                "value": default_value,
                "help": "Help text"
            }
        }
        """
        results = {}
        
        for param_name, config in parameters.items():
            param_type = config.get("type", "text_input")
            label = config.get("label", param_name.title())
            help_text = config.get("help", "")
            
            if param_type == "selectbox":
                results[param_name] = st.selectbox(
                    label,
                    options=config.get("options", []),
                    index=config.get("index", 0),
                    help=help_text
                )
            elif param_type == "number_input":
                results[param_name] = st.number_input(
                    label,
                    min_value=config.get("min_value", 0),
                    max_value=config.get("max_value", 100),
                    value=config.get("value", 0),
                    help=help_text
                )
            elif param_type == "text_input":
                results[param_name] = st.text_input(
                    label,
                    value=config.get("value", ""),
                    help=help_text
                )
            elif param_type == "checkbox":
                results[param_name] = st.checkbox(
                    label,
                    value=config.get("value", False),
                    help=help_text
                )
        
        return results