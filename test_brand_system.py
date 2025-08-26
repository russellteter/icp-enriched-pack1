#!/usr/bin/env python3
"""
Brand system consistency test for ICP Discovery Engine UI.
Tests that all brand components load correctly and styling is consistent.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all brand-related imports work correctly."""
    print("🧪 Testing brand system imports...")
    
    try:
        from src.ui.assets.brand_components import BrandComponents, ChartHelper
        print("✅ BrandComponents imported successfully")
    except Exception as e:
        print(f"❌ BrandComponents import failed: {e}")
        return False
    
    try:
        from src.ui.assets.logo import BrandLogo, LogoVariations
        print("✅ Logo components imported successfully")
    except Exception as e:
        print(f"❌ Logo import failed: {e}")
        return False
    
    try:
        from src.ui.utils.styling import StyleHelper, ThemeManager, ComponentStyler
        print("✅ Styling utilities imported successfully")
    except Exception as e:
        print(f"❌ Styling utilities import failed: {e}")
        return False
    
    return True

def test_css_file():
    """Test that CSS file exists and is readable."""
    print("\n🧪 Testing CSS file...")
    
    css_path = Path("src/ui/assets/styles.css")
    
    if not css_path.exists():
        print("❌ styles.css file not found")
        return False
    
    try:
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        if len(css_content) == 0:
            print("❌ styles.css file is empty")
            return False
        
        print(f"✅ styles.css loaded successfully ({len(css_content)} characters)")
        
        # Test for key brand elements
        brand_elements = [
            ":root",
            "--primary-purple",
            "--background-pale",
            "Inter",
            ".brand-card",
            ".stButton"
        ]
        
        missing_elements = []
        for element in brand_elements:
            if element not in css_content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"⚠️  Missing brand elements: {', '.join(missing_elements)}")
        else:
            print("✅ All key brand elements found in CSS")
        
        return len(missing_elements) == 0
        
    except Exception as e:
        print(f"❌ Error reading styles.css: {e}")
        return False

def test_brand_colors():
    """Test brand color constants."""
    print("\n🧪 Testing brand colors...")
    
    try:
        from src.ui.utils.styling import StyleHelper
        
        colors = StyleHelper.BRAND_COLORS
        required_colors = [
            "primary_purple",
            "background_pale", 
            "text_heading",
            "text_body",
            "light_purple",
            "yellow_accent",
            "card_background"
        ]
        
        missing_colors = []
        for color in required_colors:
            if color not in colors:
                missing_colors.append(color)
        
        if missing_colors:
            print(f"❌ Missing brand colors: {', '.join(missing_colors)}")
            return False
        
        # Validate color format
        for name, value in colors.items():
            if not (value.startswith("#") or value.startswith("rgba") or value.startswith("rgb")):
                print(f"⚠️  Invalid color format for {name}: {value}")
        
        print(f"✅ All {len(colors)} brand colors defined correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing brand colors: {e}")
        return False

def test_typography():
    """Test typography constants."""
    print("\n🧪 Testing typography system...")
    
    try:
        from src.ui.utils.styling import StyleHelper
        
        typography = StyleHelper.TYPOGRAPHY
        
        required_keys = ["font_family", "font_weights", "font_sizes"]
        for key in required_keys:
            if key not in typography:
                print(f"❌ Missing typography key: {key}")
                return False
        
        # Test font weights
        weights = typography["font_weights"]
        required_weights = ["light", "regular", "medium"]
        for weight in required_weights:
            if weight not in weights:
                print(f"❌ Missing font weight: {weight}")
                return False
        
        # Test font sizes
        sizes = typography["font_sizes"]
        required_sizes = ["h1", "h2", "h3", "body"]
        for size in required_sizes:
            if size not in sizes:
                print(f"❌ Missing font size: {size}")
                return False
        
        print("✅ Typography system complete")
        return True
        
    except Exception as e:
        print(f"❌ Error testing typography: {e}")
        return False

def test_layout_system():
    """Test layout constants."""
    print("\n🧪 Testing layout system...")
    
    try:
        from src.ui.utils.styling import StyleHelper
        
        layout = StyleHelper.LAYOUT
        
        required_keys = [
            "baseline",
            "gutter", 
            "outer_margin",
            "card_spacing",
            "border_radius"
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in layout:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ Missing layout keys: {', '.join(missing_keys)}")
            return False
        
        print(f"✅ Layout system complete with {len(layout)} properties")
        return True
        
    except Exception as e:
        print(f"❌ Error testing layout: {e}")
        return False

def test_logo_generation():
    """Test logo SVG generation."""
    print("\n🧪 Testing logo generation...")
    
    try:
        from src.ui.assets.logo import BrandLogo
        
        # Test basic logo generation
        logo_svg = BrandLogo.render_logo(120, show_text=True)
        
        if not logo_svg.startswith('<svg'):
            print("❌ Logo does not generate valid SVG")
            return False
        
        # Test that logo contains expected elements
        expected_elements = ["rect", "svg", "fill=\"#FFC107\"", "fill=\"#4739E7\""]
        missing_elements = []
        
        for element in expected_elements:
            if element not in logo_svg:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"⚠️  Logo missing elements: {', '.join(missing_elements)}")
        
        # Test different variants
        minimal_logo = BrandLogo.render_logo(60, style="minimal")
        icon_logo = BrandLogo.render_logo(32, style="icon")
        
        print("✅ Logo generation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing logo generation: {e}")
        return False

def test_component_methods():
    """Test key component methods."""
    print("\n🧪 Testing component methods...")
    
    try:
        from src.ui.assets.brand_components import BrandComponents, ChartHelper
        
        # Test brand tag generation
        tag_html = BrandComponents.brand_tag("Test Tag")
        if '<span class="brand-tag"' not in tag_html:
            print("❌ brand_tag method not working")
            return False
        
        # Test numbered circle
        circle_html = BrandComponents.numbered_circle(1)
        if '<span class="brand-circle"' not in circle_html:
            print("❌ numbered_circle method not working")
            return False
        
        # Test chart colors
        colors = BrandComponents.get_brand_chart_colors()
        if "primary" not in colors or "secondary" not in colors:
            print("❌ Chart colors not configured properly")
            return False
        
        # Test chart helper
        test_data = {"A": 10, "B": 20, "C": 30}
        fig = ChartHelper.create_pie_chart(test_data, "Test Chart")
        if not hasattr(fig, 'data'):
            print("❌ Chart generation not working")
            return False
        
        print("✅ Component methods working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing component methods: {e}")
        return False

def run_all_tests():
    """Run all brand system tests."""
    print("🎨 ICP Discovery Engine Brand System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("CSS File", test_css_file),
        ("Brand Colors", test_brand_colors),
        ("Typography", test_typography),
        ("Layout System", test_layout_system),
        ("Logo Generation", test_logo_generation),
        ("Component Methods", test_component_methods)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All brand system tests passed! The UI is ready for use.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the brand system implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)