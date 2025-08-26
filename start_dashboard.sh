#!/bin/bash

# ICP Discovery Engine Dashboard Startup Script
# This script starts both the FastAPI backend and the enhanced Streamlit dashboard

set -e

echo "🔍 Starting ICP Discovery Engine Dashboard..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$FASTAPI_PID" ]; then
        kill $FASTAPI_PID 2>/dev/null || true
        echo -e "${GREEN}✓ FastAPI server stopped${NC}"
    fi
    if [ ! -z "$STREAMLIT_PID" ]; then
        kill $STREAMLIT_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Streamlit dashboard stopped${NC}"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}📋 Pre-flight checks...${NC}"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check if virtual environment is recommended
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  Warning: No virtual environment detected. Consider using: python -m venv venv && source venv/bin/activate${NC}"
fi

# Check if requirements are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing requirements...${NC}"
    pip install -r requirements.txt
fi

echo -e "${GREEN}✓ Python environment ready${NC}"

# Check ports
if check_port 8080; then
    echo -e "${YELLOW}⚠️  Port 8080 is already in use. FastAPI server may already be running.${NC}"
    FASTAPI_RUNNING=true
else
    FASTAPI_RUNNING=false
fi

if check_port 8501; then
    echo -e "${RED}❌ Port 8501 is in use. Please stop the existing Streamlit app or use a different port.${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Starting services...${NC}"

# Start FastAPI server if not running
if [ "$FASTAPI_RUNNING" = false ]; then
    echo -e "${BLUE}📡 Starting FastAPI backend server...${NC}"
    python -m uvicorn src.server.app:app --host 0.0.0.0 --port 8080 --reload &
    FASTAPI_PID=$!
    
    # Wait for FastAPI to start
    echo -e "${YELLOW}⏳ Waiting for FastAPI server to start...${NC}"
    sleep 5
    
    # Check if FastAPI started successfully
    if check_port 8080; then
        echo -e "${GREEN}✓ FastAPI server started on http://localhost:8080${NC}"
    else
        echo -e "${RED}❌ Failed to start FastAPI server${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ FastAPI server already running on http://localhost:8080${NC}"
    FASTAPI_PID=""
fi

# Start Streamlit dashboard
echo -e "${BLUE}🎨 Starting Streamlit dashboard...${NC}"
python -m streamlit run src/ui/dashboard.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

# Wait for Streamlit to start
echo -e "${YELLOW}⏳ Waiting for Streamlit dashboard to start...${NC}"
sleep 3

# Check if Streamlit started successfully
if check_port 8501; then
    echo -e "${GREEN}✓ Streamlit dashboard started on http://localhost:8501${NC}"
else
    echo -e "${RED}❌ Failed to start Streamlit dashboard${NC}"
    cleanup
    exit 1
fi

# Display startup summary
echo -e "\n${GREEN}🎉 ICP Discovery Engine Dashboard is ready!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📊 Dashboard:    ${NC}http://localhost:8501"
echo -e "${GREEN}🔧 API Server:   ${NC}http://localhost:8080"
echo -e "${GREEN}📖 API Docs:     ${NC}http://localhost:8080/docs"
echo -e "${GREEN}💊 Health Check: ${NC}http://localhost:8080/health"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${YELLOW}💡 Tips:${NC}"
echo -e "   • Open http://localhost:8501 to access the dashboard"
echo -e "   • Use Ctrl+C to stop both services"
echo -e "   • Check server logs above for any startup issues"
echo -e "   • Run 'make eval' to test the system after workflows"

echo -e "\n${BLUE}⏳ Services running... Press Ctrl+C to stop${NC}"

# Wait for both processes
wait