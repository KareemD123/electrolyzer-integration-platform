#!/bin/bash

# Electrolyzer Integration Toolkit - Development Server Startup Script
# This script starts both the backend (FastAPI) and frontend (Vite) servers

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Electrolyzer Integration Toolkit${NC}"
echo -e "${BLUE}Starting Development Servers${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}Backend virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    cd ..
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Frontend dependencies not found. Installing...${NC}"
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

echo ""
echo -e "${GREEN}Starting Backend Server...${NC}"
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | tee ../backend.log | sed "s/^/[${GREEN}BACKEND${NC}] /" &
BACKEND_PID=$!
deactivate
cd ..
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

echo ""
echo -e "${GREEN}Starting Frontend Server...${NC}"
cd frontend
npm run dev 2>&1 | tee ../frontend.log | sed "s/^/[${BLUE}FRONTEND${NC}] /" &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All servers running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Logs are displayed below and saved to:${NC}"
echo -e "  backend.log"
echo -e "  frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo ""

# Wait for both processes
wait
