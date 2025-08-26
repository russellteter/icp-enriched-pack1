#!/usr/bin/env python3
"""
Simple brand system test for CSS and file structure validation.
"""

from pathlib import Path
import json

def test_file_structure():
    """Test that all required brand files exist."""
    print("🧪 Testing brand file structure...")
    
    required_files = [
        "src/ui/assets/styles.css",
        "src/ui/assets/brand_components.py",
        "src/ui/assets/logo.py",
        "src/ui/utils/styling.py",
        "src/ui/dashboard.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print(f"✅ All {len(required_files)} brand files exist")
    return True

def test_css_content():
    """Test CSS file contains key brand elements."""
    print("\n🧪 Testing CSS content...")
    
    css_path = Path("src/ui/assets/styles.css")
    if not css_path.exists():
        print("❌ CSS file not found")
        return False
    
    with open(css_path, 'r') as f:
        css_content = f.read()
    
    # Test for key brand elements
    required_elements = [
        ":root {",
        "--primary-purple: #4739E7",
        "--background-pale: #EDECFD",
        "--text-heading: #0A1849",
        "--text-body: #0E0E1E", 
        "--light-purple: #DAD7FA",
        "--yellow-accent: #FFBA00",
        "--card-background: #FFFFFF",
        "font-family: 'Inter'",
        ".brand-card {",
        ".stButton > button {",
        "@import url('https://fonts.googleapis.com/css2?family=Inter"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in css_content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing CSS elements: {missing_elements[:3]}...")
        return False
    
    print("✅ All key CSS brand elements found")
    return True

def test_component_files():
    """Test that component files contain expected classes and functions."""
    print("\n🧪 Testing component files...")
    
    # Test brand_components.py
    brand_components_path = Path("src/ui/assets/brand_components.py")
    if brand_components_path.exists():
        with open(brand_components_path, 'r') as f:
            content = f.read()
        
        required_classes_funcs = [
            "class BrandComponents:",
            "def load_brand_css",
            "def render_logo",
            "def brand_button",
            "def brand_card",
            "class ChartHelper:"
        ]
        
        missing = []
        for item in required_classes_funcs:
            if item not in content:
                missing.append(item)
        
        if missing:
            print(f"❌ Missing in brand_components.py: {missing}")
            return False
    
    # Test logo.py
    logo_path = Path("src/ui/assets/logo.py")
    if logo_path.exists():
        with open(logo_path, 'r') as f:
            content = f.read()
        
        required_items = [
            "class BrandLogo:",
            "def render_logo",
            "svg width=",
            "fill=\"#FFC107\"",
            "fill=\"#4739E7\""
        ]
        
        missing = []
        for item in required_items:
            if item not in content:
                missing.append(item)
        
        if missing:
            print(f"❌ Missing in logo.py: {missing}")
            return False
    
    print("✅ Component files contain expected elements")
    return True

def test_dashboard_integration():
    """Test that dashboard.py uses brand components."""
    print("\n🧪 Testing dashboard brand integration...")
    
    dashboard_path = Path("src/ui/dashboard.py")
    if not dashboard_path.exists():
        print("❌ Dashboard file not found")
        return False
    
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    brand_integrations = [
        "from .assets.brand_components import BrandComponents",
        "from .assets.logo import BrandLogo",
        "BrandComponents.load_brand_css()",
        "BrandLogo.set_page_favicon()",
        "BrandComponents.section_header",
        "BrandComponents.brand_button"
    ]
    
    missing = []
    for integration in brand_integrations:
        if integration not in content:
            missing.append(integration)
    
    if missing:
        print(f"❌ Missing dashboard integrations: {missing[:3]}...")
        return False
    
    print("✅ Dashboard properly integrated with brand system")
    return True

def test_color_consistency():
    """Test color values are consistent across files.""" 
    print("\n🧪 Testing color consistency...")
    
    # Check CSS colors
    css_path = Path("src/ui/assets/styles.css")
    with open(css_path, 'r') as f:
        css_content = f.read()
    
    # Key colors that should be consistent
    brand_colors = {
        "primary_purple": "#4739E7",
        "yellow_accent": "#FFBA00", 
        "background_pale": "#EDECFD",
        "text_heading": "#0A1849"
    }
    
    inconsistencies = []
    for color_name, color_value in brand_colors.items():
        css_var = f"--{color_name.replace('_', '-')}: {color_value}"
        if css_var not in css_content:
            inconsistencies.append(f"{color_name} -> {color_value}")
    
    # Check logo colors
    logo_path = Path("src/ui/assets/logo.py")
    if logo_path.exists():
        with open(logo_path, 'r') as f:
            logo_content = f.read()
        
        if '#FFC107' not in logo_content or '#4739E7' not in logo_content:
            inconsistencies.append("Logo colors")
    
    if inconsistencies:
        print(f"❌ Color inconsistencies found: {inconsistencies}")
        return False
    
    print("✅ Brand colors consistent across files")
    return True

def test_typography_system():
    """Test typography implementation."""
    print("\n🧪 Testing typography system...")
    
    css_path = Path("src/ui/assets/styles.css") 
    with open(css_path, 'r') as f:
        css_content = f.read()
    
    typography_elements = [
        "font-family: 'Inter'",
        "--font-weight-light: 300",   # Light weight definition
        "--font-weight-regular: 400", # Regular weight definition  
        "--font-weight-medium: 500",  # Medium weight definition
        "font-size: 48px",   # H1
        "font-size: 32px",   # H2
        "font-size: 20px",   # H3
        "font-size: 16px"    # Body
    ]
    
    missing = []
    for element in typography_elements:
        if element not in css_content:
            missing.append(element)
    
    if missing:
        print(f"❌ Missing typography elements: {missing[:3]}...")
        return False
    
    print("✅ Typography system properly implemented")
    return True

def run_tests():
    """Run all brand tests."""
    print("🎨 ICP Discovery Engine Brand System Validation")
    print("=" * 55)
    
    tests = [
        ("File Structure", test_file_structure),
        ("CSS Content", test_css_content), 
        ("Component Files", test_component_files),
        ("Dashboard Integration", test_dashboard_integration),
        ("Color Consistency", test_color_consistency),
        ("Typography System", test_typography_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 55)
    print("📋 VALIDATION SUMMARY:")
    print("=" * 55)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL" 
        print(f"{status} - {test_name}")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 Brand system validation successful!")
        print("🚀 The UI is ready with complete brand styling!")
        return True
    else:
        print(f"\n⚠️  {failed} validation(s) failed. Please review implementation.")
        return False

if __name__ == "__main__":
    run_tests()