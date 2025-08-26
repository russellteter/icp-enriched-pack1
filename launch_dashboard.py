#!/usr/bin/env python3
"""
Main launcher for the ICP Discovery Engine UI.
Now defaults to the modern, clean interface.
"""
import sys
import os
import subprocess
from pathlib import Path

def main():
    """Launch the modern ICP Discovery Engine UI."""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    ui_app_path = script_dir / "src" / "ui" / "modern_app.py"
    
    # Check if the modern app exists
    if not ui_app_path.exists():
        print(f"❌ Modern UI app not found at: {ui_app_path}")
        print("Falling back to legacy dashboard...")
        try:
            from src.ui.dashboard import main as legacy_main
            legacy_main()
            return
        except Exception as e:
            print(f"❌ Legacy dashboard also failed: {e}")
            sys.exit(1)
    
    print("🚀 Starting Modern ICP Discovery Engine UI...")
    print("📍 URL: http://localhost:8501")
    print("💡 To stop, press Ctrl+C")
    print("🔧 For legacy dashboard: python launch_legacy_dashboard.py")
    print()
    
    try:
        # Change to the UI directory so imports work correctly
        os.chdir(script_dir / "src" / "ui")
        
        # Launch Streamlit with the modern app
        subprocess.run([
            sys.executable, 
            "-m", 
            "streamlit", 
            "run", 
            "modern_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--theme.base", "light",
            "--theme.primaryColor", "#4739E7",
            "--theme.backgroundColor", "#f9fafb",
            "--theme.secondaryBackgroundColor", "#ffffff",
            "--theme.textColor", "#111827",
            "--server.headless", "false"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Modern UI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Modern UI: {e}")
        print("🔧 Try running: python launch_legacy_dashboard.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()