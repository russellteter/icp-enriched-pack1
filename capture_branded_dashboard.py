#!/usr/bin/env python3
"""
Use Playwright MCP to capture screenshots of the branded ICP Discovery Engine dashboard.
"""

import asyncio
import json
from pathlib import Path
import subprocess
import time

def check_dashboard_running():
    """Check if the dashboard is running on any common ports."""
    ports_to_check = [8501, 8502, 8503, 8504]
    
    for port in ports_to_check:
        try:
            result = subprocess.run(['curl', '-s', f'http://localhost:{port}'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0 and 'ICP Discovery Engine' in result.stdout.decode():
                print(f"✅ Found dashboard running on port {port}")
                return f"http://localhost:{port}"
        except:
            continue
    
    return None

def launch_dashboard():
    """Launch the branded dashboard if not already running."""
    dashboard_url = check_dashboard_running()
    
    if dashboard_url:
        return dashboard_url
    
    print("🚀 Launching branded dashboard...")
    
    # Try to launch on port 8505
    try:
        subprocess.Popen([
            'python', '-m', 'streamlit', 'run', 
            'launch_dashboard.py', 
            '--server.port=8505',
            '--server.headless=true'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for startup
        print("⏳ Waiting for dashboard to start...")
        time.sleep(10)
        
        # Check if it's running
        for _ in range(6):  # Try for 30 seconds
            try:
                result = subprocess.run(['curl', '-s', 'http://localhost:8505'], 
                                      capture_output=True, timeout=3)
                if result.returncode == 0:
                    print("✅ Dashboard launched successfully on port 8505")
                    return "http://localhost:8505"
            except:
                pass
            time.sleep(5)
            
    except Exception as e:
        print(f"❌ Failed to launch dashboard: {e}")
    
    return None

async def capture_with_playwright_mcp():
    """Use Playwright MCP to capture the branded dashboard."""
    
    # First, ensure dashboard is running
    dashboard_url = launch_dashboard()
    
    if not dashboard_url:
        print("❌ Could not find or launch the branded dashboard")
        print("Please manually start it with: python -m streamlit run launch_dashboard.py")
        return
    
    print(f"🎨 Capturing branded dashboard at {dashboard_url}")
    
    # Create screenshots directory
    screenshots_dir = Path("dashboard_screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Instructions for manual Playwright MCP usage
    print(f"""
🎨 Branded Dashboard Ready for Screenshots!

Dashboard URL: {dashboard_url}

To capture screenshots with Playwright MCP, you can now:

1. 📸 Take full page screenshot:
   - Navigate to: {dashboard_url}
   - Take screenshot of the main dashboard with your brand styling

2. 🎯 Capture individual tabs:
   - Discover tab: Workflow configuration with purple buttons
   - Analyze tab: Brand charts and data visualization  
   - Monitor tab: System health with brand indicators
   - History tab: Historical analysis with consistent styling

3. 🎨 Focus areas to capture:
   - Header with geometric logo (golden yellow + purple squares)
   - Brand color scheme (#4739E7 purple throughout)
   - Inter typography and professional layout
   - Purple buttons and brand cards
   - Data tables with purple headers

The dashboard showcases your complete brand system!
""")

def main():
    """Main function to capture the branded dashboard."""
    print("🎨 ICP Discovery Engine - Brand Dashboard Capture")
    print("=" * 55)
    
    try:
        asyncio.run(capture_with_playwright_mcp())
    except KeyboardInterrupt:
        print("\n🛑 Capture process interrupted")
    except Exception as e:
        print(f"❌ Error during capture: {e}")

if __name__ == "__main__":
    main()