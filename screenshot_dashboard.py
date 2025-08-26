#!/usr/bin/env python3
"""
Screenshot the branded ICP Discovery Engine dashboard.
"""
import asyncio
from playwright.async_api import async_playwright
import time
from pathlib import Path

async def screenshot_dashboard():
    """Take screenshots of the branded dashboard."""
    print("🎨 Taking screenshots of your branded dashboard...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to False so you can see what's happening
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        try:
            # Navigate to dashboard
            print("📡 Connecting to dashboard at http://localhost:8503...")
            await page.goto("http://localhost:8503", wait_until="networkidle", timeout=30000)
            
            # Wait for the page to fully load
            await page.wait_for_selector("h1", timeout=10000)
            await asyncio.sleep(3)  # Extra time for CSS/fonts to load
            
            # Take screenshot of main dashboard
            print("📸 Taking full dashboard screenshot...")
            await page.screenshot(path="dashboard_main.png", full_page=True)
            print("✅ Saved dashboard_main.png")
            
            # Take screenshot of each tab
            tabs = ["🚀 Discover", "📊 Analyze", "📈 Monitor", "📁 History"]
            
            for tab in tabs:
                try:
                    print(f"📸 Taking screenshot of {tab} tab...")
                    
                    # Click the tab
                    tab_selector = f"button[data-baseweb='tab']:has-text('{tab}')"
                    await page.click(tab_selector)
                    await asyncio.sleep(2)  # Wait for tab content to load
                    
                    # Take screenshot
                    filename = f"dashboard_{tab.split(' ')[1].lower()}.png"
                    await page.screenshot(path=filename, full_page=True)
                    print(f"✅ Saved {filename}")
                    
                except Exception as e:
                    print(f"⚠️  Could not screenshot {tab} tab: {e}")
            
            # Take a screenshot of just the header/logo area
            print("📸 Taking logo/header screenshot...")
            header = await page.query_selector("h1")
            if header:
                await header.screenshot(path="dashboard_header.png")
                print("✅ Saved dashboard_header.png")
            
            print("\n🎉 Screenshots complete!")
            print("Files created:")
            for img_file in Path(".").glob("dashboard_*.png"):
                print(f"  📁 {img_file}")
            
        except Exception as e:
            print(f"❌ Error taking screenshots: {e}")
            print("Make sure your dashboard is running at http://localhost:8503")
            
        finally:
            await browser.close()

def main():
    """Run the screenshot function."""
    try:
        asyncio.run(screenshot_dashboard())
    except KeyboardInterrupt:
        print("\n🛑 Screenshot process interrupted by user")
    except Exception as e:
        print(f"❌ Failed to take screenshots: {e}")

if __name__ == "__main__":
    main()