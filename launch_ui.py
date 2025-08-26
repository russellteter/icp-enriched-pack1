#!/usr/bin/env python3
"""
Interactive UI launcher for ICP Discovery Engine.
Allows users to choose between Modern UI (clean) and Legacy Dashboard (complex).
"""

import sys
import subprocess
import os
from pathlib import Path


def show_interface_options():
    """Display interface selection menu."""
    print("🎯 ICP Discovery Engine - Interface Selection")
    print("=" * 50)
    print()
    print("Choose your interface:")
    print()
    print("1. 🌟 Modern UI (Recommended)")
    print("   - Clean, simple design")
    print("   - 3-step wizard workflow") 
    print("   - Single-purpose screens")
    print("   - Mobile responsive")
    print("   - Perfect for end users")
    print()
    print("2. 🔧 Legacy Dashboard")
    print("   - Multi-tab interface")
    print("   - All features visible")
    print("   - Complex configuration")
    print("   - System monitoring")
    print("   - Good for debugging")
    print()
    print("3. ❓ Help - Which should I choose?")
    print()
    print("0. Exit")
    print()


def show_help():
    """Show help for interface selection."""
    print()
    print("🤔 Which Interface Should You Choose?")
    print("=" * 40)
    print()
    print("🌟 Choose Modern UI if you:")
    print("   • Want a clean, user-friendly experience")
    print("   • Are new to the system")
    print("   • Need to run discoveries quickly")
    print("   • Want guided setup with smart defaults")
    print("   • Are demonstrating to customers/stakeholders")
    print()
    print("🔧 Choose Legacy Dashboard if you:")
    print("   • Need to monitor system metrics")
    print("   • Want all options visible at once")
    print("   • Are debugging or troubleshooting")
    print("   • Need detailed analytics and monitoring")
    print("   • Prefer complex, information-dense interfaces")
    print()
    print("💡 Recommendation: Start with Modern UI - it's cleaner and easier!")
    print()
    input("Press Enter to return to selection menu...")


def launch_modern_ui():
    """Launch the modern UI interface."""
    script_dir = Path(__file__).parent
    
    print("🚀 Starting Modern ICP Discovery Engine UI...")
    print("📍 URL: http://localhost:8501")
    print("💡 Press Ctrl+C to stop")
    print()
    
    try:
        os.chdir(script_dir / "src" / "ui")
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
            "--theme.textColor", "#111827"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Modern UI stopped by user")
    except Exception as e:
        print(f"❌ Failed to start Modern UI: {e}")
        sys.exit(1)


def launch_legacy_dashboard():
    """Launch the legacy dashboard interface."""
    print("🔧 Starting Legacy ICP Discovery Engine Dashboard...")
    print("📍 URL: http://localhost:8501") 
    print("💡 Press Ctrl+C to stop")
    print()
    
    try:
        from src.ui.dashboard import main
        main()
    except Exception as e:
        print(f"❌ Failed to start Legacy Dashboard: {e}")
        sys.exit(1)


def main():
    """Main interface selection loop."""
    
    while True:
        show_interface_options()
        
        try:
            choice = input("Enter your choice (1-3, 0 to exit): ").strip()
            
            if choice == "1":
                launch_modern_ui()
                break
            elif choice == "2":
                launch_legacy_dashboard() 
                break
            elif choice == "3":
                show_help()
                continue
            elif choice == "0":
                print("👋 Goodbye!")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 0.")
                print()
                input("Press Enter to continue...")
                continue
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()