#!/bin/bash

echo "🚀 Starting ICP Discovery Engine - Simple Interface"
echo "=================================================="

# Activate virtual environment
source .venv/bin/activate

# Start the server in the background
echo "📡 Starting server..."
uvicorn src.server.app:app --host 0.0.0.0 --port 8080 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Check if server is running
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Server is running on http://localhost:8080"
else
    echo "❌ Server failed to start"
    exit 1
fi

# Start the web interface
echo "🌐 Starting web interface..."
echo "📱 Opening browser to http://localhost:8501"
echo ""
echo "🎯 Your tool is ready! Use the web interface to:"
echo "   - Select Healthcare, Corporate, or Providers segments"
echo "   - Set target count and mode"
echo "   - Click 'Start Discovery' to find organizations"
echo "   - Download results as CSV"
echo ""
echo "💡 Press Ctrl+C to stop both server and interface"
echo ""

# Start Streamlit
streamlit run simple_web_interface.py --server.port 8501 --server.address localhost

# Cleanup when Streamlit stops
echo "🛑 Stopping server..."
kill $SERVER_PID
echo "✅ Done!"



