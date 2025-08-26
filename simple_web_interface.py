#!/usr/bin/env python3
"""
Simple Web Interface for ICP Discovery Engine
Run this locally to test your tool immediately!
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="ICP Discovery Engine",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 ICP Discovery Engine")
st.markdown("**Find Healthcare, Corporate Academies, and Training Providers**")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Segment selection
segment = st.sidebar.selectbox(
    "Select Segment:",
    ["healthcare", "corporate", "providers"],
    help="Choose which type of organizations to discover"
)

# Target count
target_count = st.sidebar.slider(
    "Target Count:",
    min_value=1,
    max_value=20,
    value=5,
    help="Number of results to find"
)

# Mode selection
mode = st.sidebar.selectbox(
    "Mode:",
    ["fast", "deep"],
    help="Fast for quick results, Deep for comprehensive search"
)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"Discovering {segment.title()} Organizations")
    
    # Run button
    if st.button("🚀 Start Discovery", type="primary", use_container_width=True):
        with st.spinner(f"Searching for {target_count} {segment} organizations..."):
            try:
                # Prepare request
                payload = {
                    "segment": segment,
                    "targetcount": target_count,
                    "mode": mode
                }
                
                # Make request to local server
                response = requests.post(
                    "http://localhost:8080/run",
                    json=payload,
                    timeout=300  # 5 minutes timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display results
                    st.success(f"✅ Found {result.get('count', 0)} organizations!")
                    
                    # Show summary
                    if 'summary' in result:
                        st.info(f"**Summary:** {result['summary']}")
                    
                    # Show budget info
                    if 'budget' in result:
                        budget = result['budget']
                        st.metric("Searches Used", f"{budget.get('searches', 0)}")
                        st.metric("Fetches Used", f"{budget.get('fetches', 0)}")
                        st.metric("Enrichments Used", f"{budget.get('enrich', 0)}")
                    
                    # Display results in a table
                    if 'outputs' in result and result['outputs']:
                        st.subheader("📊 Results")
                        
                        # Convert to DataFrame
                        df_data = []
                        for item in result['outputs']:
                            df_data.append({
                                'Organization': item.get('organization', ''),
                                'Tier': item.get('tier', ''),
                                'Score': item.get('score', 0),
                                'Region': item.get('region', ''),
                                'Evidence URL': item.get('evidence_url', ''),
                                'Notes': item.get('notes', '')
                            })
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Results as CSV",
                            data=csv,
                            file_name=f"{segment}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No results found. Try adjusting your parameters.")
                        
                else:
                    st.error(f"❌ Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to server. Make sure the server is running on localhost:8080")
                st.info("💡 To start the server, run: `uvicorn src.server.app:app --host 0.0.0.0 --port 8080`")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with col2:
    st.header("📋 Quick Actions")
    
    # Health check
    if st.button("🏥 Check Server Health"):
        try:
            response = requests.get("http://localhost:8080/health", timeout=10)
            if response.status_code == 200:
                st.success("✅ Server is healthy!")
            else:
                st.error("❌ Server health check failed")
        except:
            st.error("❌ Cannot connect to server")
    
    # Status check
    if st.button("📊 Check Server Status"):
        try:
            response = requests.get("http://localhost:8080/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                st.json(status)
            else:
                st.error("❌ Status check failed")
        except:
            st.error("❌ Cannot connect to server")

# Footer
st.markdown("---")
st.markdown("**Instructions:**")
st.markdown("1. Make sure your server is running: `uvicorn src.server.app:app --host 0.0.0.0 --port 8080`")
st.markdown("2. Select your segment and parameters")
st.markdown("3. Click 'Start Discovery' to find organizations")
st.markdown("4. Download results as CSV")

# Auto-refresh
if st.button("🔄 Refresh Page"):
    st.rerun()

if __name__ == "__main__":
    pass



