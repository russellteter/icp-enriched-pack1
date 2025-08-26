#!/usr/bin/env python3
"""
Simple test script for the modern UI components.
"""

import sys
import os

# Add the UI directory to path
ui_dir = os.path.join(os.path.dirname(__file__), 'src', 'ui')
sys.path.insert(0, ui_dir)

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        print("🧪 Testing imports...")
        
        from components.modern_components import ModernComponents, ModernNavigation
        print("✅ ModernComponents imported")
        
        from utils.api_client import ICPApiClient, RunRequest, Segment, Mode, Region
        print("✅ API client imported")
        
        from screens.home import render_home_screen
        print("✅ Home screen imported")
        
        from screens.setup import render_setup_screen
        print("✅ Setup screen imported")
        
        from screens.progress import render_progress_screen
        print("✅ Progress screen imported")
        
        from screens.results import render_results_screen
        print("✅ Results screen imported")
        
        import modern_app
        print("✅ Modern app imported")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_api_client():
    """Test basic API client functionality."""
    try:
        print("\n🧪 Testing API client...")
        
        from utils.api_client import ICPApiClient
        client = ICPApiClient()
        
        # Test health check (will fail if server not running, but shouldn't crash)
        success, result = client.health_check()
        if success:
            print("✅ API server is running and responsive")
        else:
            print(f"⚠️ API server not available: {result.message}")
        
        print("✅ API client basic functionality works")
        return True
        
    except Exception as e:
        print(f"❌ API client test failed: {e}")
        return False


def test_run_request():
    """Test creating RunRequest objects."""
    try:
        print("\n🧪 Testing RunRequest creation...")
        
        from utils.api_client import RunRequest, Segment, Mode, Region
        
        # Create a sample request
        request = RunRequest(
            segment=Segment.HEALTHCARE,
            targetcount=10,
            mode=Mode.FAST,
            region=Region.NA
        )
        
        print(f"✅ RunRequest created: {request.segment.value}, {request.targetcount} targets")
        return True
        
    except Exception as e:
        print(f"❌ RunRequest test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Modern ICP Discovery UI")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_api_client,
        test_run_request
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The modern UI is ready to launch.")
        print("\nTo start the modern UI:")
        print("  python launch_modern_ui.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()