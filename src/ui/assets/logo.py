"""
Brand logo component for ICP Discovery Engine.
Creates the geometric squares logo design with golden yellow and purple colors.
"""

import streamlit as st
from typing import Optional


class BrandLogo:
    """Brand logo component with geometric squares design."""
    
    @staticmethod
    def render_logo(
        size: int = 120,
        show_text: bool = True,
        text: str = "ICP",
        style: str = "default"
    ) -> str:
        """
        Render the brand logo SVG.
        
        Args:
            size: Logo size in pixels (default 120x120)
            show_text: Whether to show text overlay (default True)
            text: Text to display (default "ICP")
            style: Logo style variant ("default", "minimal", "icon")
        
        Returns:
            SVG string for the logo
        """
        if style == "minimal":
            return BrandLogo._render_minimal_logo(size)
        elif style == "icon":
            return BrandLogo._render_icon_logo(size)
        else:
            return BrandLogo._render_default_logo(size, show_text, text)
    
    @staticmethod
    def _render_default_logo(size: int, show_text: bool, text: str) -> str:
        """Render the default full logo with squares and optional text."""
        text_element = ""
        if show_text:
            text_size = max(16, size // 5)
            text_element = f'''
            <text x="{size//2}" y="{size//2 + text_size//3}" 
                  text-anchor="middle" 
                  fill="#4739E7" 
                  font-family="Inter, sans-serif" 
                  font-weight="500" 
                  font-size="{text_size}">{text}</text>
            '''
        
        # Calculate proportional dimensions
        large_square_size = size * 0.5  # 60px for 120px logo
        small_square_size = size * 0.21  # 25px for 120px logo
        large_square_pos = size * 0.25  # 30px for 120px logo
        small_square_offset = size * 0.083  # 10px for 120px logo
        small_square_far = size * 0.708  # 85px for 120px logo
        stroke_width = max(1, size // 60)  # 2px for 120px logo
        border_radius = max(2, size // 20)  # 6px for 120px logo
        small_radius = max(1, size // 40)  # 3px for 120px logo
        
        return f'''
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
            <!-- Drop shadow filter -->
            <defs>
                <filter id="shadow{size}" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="2" dy="2" stdDeviation="2" flood-color="rgba(0,0,0,0.1)"/>
                </filter>
            </defs>
            
            <!-- Large central square in golden yellow -->
            <rect x="{large_square_pos}" y="{large_square_pos}" 
                  width="{large_square_size}" height="{large_square_size}" 
                  fill="#FFC107" 
                  stroke="#4739E7" 
                  stroke-width="{stroke_width}" 
                  rx="{border_radius}"
                  filter="url(#shadow{size})"/>
            
            <!-- Top-left small square in purple -->
            <rect x="{small_square_offset}" y="{small_square_offset}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{small_radius}"
                  filter="url(#shadow{size})"/>
            
            <!-- Top-right small square in purple -->
            <rect x="{small_square_far}" y="{small_square_offset}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{small_radius}"
                  filter="url(#shadow{size})"/>
            
            <!-- Bottom-right small square in purple -->
            <rect x="{small_square_far}" y="{small_square_far}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{small_radius}"
                  filter="url(#shadow{size})"/>
            
            {text_element}
        </svg>
        '''
    
    @staticmethod
    def _render_minimal_logo(size: int) -> str:
        """Render a minimal version without text or shadows."""
        large_square_size = size * 0.5
        small_square_size = size * 0.21
        large_square_pos = size * 0.25
        small_square_offset = size * 0.083
        small_square_far = size * 0.708
        border_radius = max(2, size // 20)
        small_radius = max(1, size // 40)
        
        return f'''
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
            <!-- Large central square -->
            <rect x="{large_square_pos}" y="{large_square_pos}" 
                  width="{large_square_size}" height="{large_square_size}" 
                  fill="#FFC107" 
                  rx="{border_radius}"/>
            
            <!-- Small squares -->
            <rect x="{small_square_offset}" y="{small_square_offset}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{small_radius}"/>
            <rect x="{small_square_far}" y="{small_square_offset}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{small_radius}"/>
            <rect x="{small_square_far}" y="{small_square_far}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{small_radius}"/>
        </svg>
        '''
    
    @staticmethod
    def _render_icon_logo(size: int) -> str:
        """Render a simplified icon version for small sizes."""
        # Simplified proportions for icon
        large_square_size = size * 0.6
        small_square_size = size * 0.25
        large_square_pos = size * 0.2
        small_square_offset = size * 0.05
        small_square_far = size * 0.7
        border_radius = max(1, size // 30)
        
        return f'''
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
            <rect x="{large_square_pos}" y="{large_square_pos}" 
                  width="{large_square_size}" height="{large_square_size}" 
                  fill="#FFC107" 
                  rx="{border_radius}"/>
            <rect x="{small_square_offset}" y="{small_square_offset}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{border_radius}"/>
            <rect x="{small_square_far}" y="{small_square_offset}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{border_radius}"/>
            <rect x="{small_square_far}" y="{small_square_far}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="#4739E7" 
                  rx="{border_radius}"/>
        </svg>
        '''
    
    @staticmethod
    def display_logo(
        size: int = 120,
        show_text: bool = True,
        text: str = "ICP",
        style: str = "default",
        center: bool = False
    ) -> None:
        """
        Display the logo in Streamlit.
        
        Args:
            size: Logo size in pixels
            show_text: Whether to show text overlay
            text: Text to display
            style: Logo style variant
            center: Whether to center the logo
        """
        logo_svg = BrandLogo.render_logo(size, show_text, text, style)
        
        if center:
            st.markdown(f'''
            <div style="display: flex; justify-content: center; margin: 20px 0;">
                {logo_svg}
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(logo_svg, unsafe_allow_html=True)
    
    @staticmethod
    def logo_with_title(
        title: str,
        subtitle: str = "",
        logo_size: int = 80,
        center: bool = True
    ) -> None:
        """
        Display logo with title and optional subtitle.
        
        Args:
            title: Main title text
            subtitle: Optional subtitle text
            logo_size: Size of the logo
            center: Whether to center the content
        """
        if center:
            col1, col2, col3 = st.columns([1, 2, 1])
            container = col2
        else:
            container = st
            
        with container:
            # Logo
            BrandLogo.display_logo(logo_size, show_text=False, center=center)
            
            # Title and subtitle
            title_style = "text-align: center;" if center else ""
            st.markdown(f'''
            <div style="{title_style}">
                <h1 style="color: #0A1849; font-weight: 300; margin: 20px 0 10px 0;">{title}</h1>
                {f'<p style="color: #0E0E1E; font-size: 18px; margin: 0 0 20px 0;">{subtitle}</p>' if subtitle else ''}
            </div>
            ''', unsafe_allow_html=True)
    
    @staticmethod
    def favicon_data_uri(size: int = 32) -> str:
        """
        Generate a data URI for use as favicon.
        
        Args:
            size: Size for the favicon (typically 16, 32, or 64)
            
        Returns:
            Data URI string for the favicon
        """
        logo_svg = BrandLogo.render_logo(size, show_text=False, style="icon")
        import base64
        
        # Encode SVG as base64
        svg_bytes = logo_svg.encode('utf-8')
        svg_b64 = base64.b64encode(svg_bytes).decode('utf-8')
        
        return f"data:image/svg+xml;base64,{svg_b64}"
    
    @staticmethod
    def set_page_favicon(size: int = 32) -> None:
        """
        Set the page favicon using the brand logo.
        
        Args:
            size: Size for the favicon
        """
        favicon_uri = BrandLogo.favicon_data_uri(size)
        st.markdown(f'''
        <link rel="icon" type="image/svg+xml" href="{favicon_uri}">
        ''', unsafe_allow_html=True)


class LogoVariations:
    """Additional logo variations and utilities."""
    
    @staticmethod
    def horizontal_logo(height: int = 60, include_text: bool = True) -> str:
        """Create a horizontal layout logo for headers."""
        logo_size = height
        text_size = height * 0.4
        total_width = logo_size + (120 if include_text else 0)
        
        text_element = ""
        if include_text:
            text_element = f'''
            <text x="{logo_size + 20}" y="{height//2 + text_size//3}" 
                  fill="#0A1849" 
                  font-family="Inter, sans-serif" 
                  font-weight="300" 
                  font-size="{text_size}">ICP Discovery Engine</text>
            '''
        
        logo_svg = BrandLogo.render_logo(logo_size, show_text=False, style="minimal")
        
        return f'''
        <svg width="{total_width}" height="{height}" viewBox="0 0 {total_width} {height}" xmlns="http://www.w3.org/2000/svg">
            <g>{logo_svg.replace(f'<svg width="{logo_size}" height="{logo_size}" viewBox="0 0 {logo_size} {logo_size}" xmlns="http://www.w3.org/2000/svg">', '').replace('</svg>', '')}</g>
            {text_element}
        </svg>
        '''
    
    @staticmethod
    def loading_logo(size: int = 60) -> str:
        """Create an animated loading version of the logo."""
        return f'''
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <style>
                    .loading-squares {{
                        animation: pulse 2s ease-in-out infinite;
                    }}
                    @keyframes pulse {{
                        0%, 100% {{ opacity: 1; }}
                        50% {{ opacity: 0.3; }}
                    }}
                </style>
            </defs>
            {BrandLogo._render_minimal_logo(size).replace('<svg', '<g').replace('</svg>', '</g>').replace('<rect', '<rect class="loading-squares"')}
        </svg>
        '''
    
    @staticmethod
    def monochrome_logo(size: int = 120, color: str = "#4739E7") -> str:
        """Create a monochrome version of the logo."""
        large_square_size = size * 0.5
        small_square_size = size * 0.21
        large_square_pos = size * 0.25
        small_square_offset = size * 0.083
        small_square_far = size * 0.708
        border_radius = max(2, size // 20)
        small_radius = max(1, size // 40)
        
        return f'''
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
            <rect x="{large_square_pos}" y="{large_square_pos}" 
                  width="{large_square_size}" height="{large_square_size}" 
                  fill="{color}" 
                  opacity="0.8"
                  rx="{border_radius}"/>
            <rect x="{small_square_offset}" y="{small_square_offset}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="{color}" 
                  rx="{small_radius}"/>
            <rect x="{small_square_far}" y="{small_square_offset}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="{color}" 
                  rx="{small_radius}"/>
            <rect x="{small_square_far}" y="{small_square_far}" 
                  width="{small_square_size}" height="{small_square_size}" 
                  fill="{color}" 
                  rx="{small_radius}"/>
        </svg>
        '''