#!/usr/bin/env python3
"""
Legacy launcher for the original complex ICP Discovery Engine dashboard.
This is the multi-tab interface that was replaced by the modern UI.
Use this for backward compatibility or if you need the complex interface.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the legacy dashboard
try:
    print("🔧 Starting Legacy ICP Discovery Engine Dashboard...")
    print("⚠️  Note: This is the legacy multi-tab interface")
    print("💡 For the modern, clean interface use: python launch_dashboard.py")
    print("📍 URL: http://localhost:8501")
    print()
    
    from src.ui.dashboard import main
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    print(f"❌ Error launching legacy dashboard: {e}")
    print("Make sure all dependencies are installed: pip install streamlit plotly pandas")
    sys.exit(1)