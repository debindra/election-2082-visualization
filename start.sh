#!/bin/bash
# Startup script for Election Data API and Frontend

echo "Starting Election Data Application..."
echo "======================================"

# Function to handle cleanup on script exit
cleanup() {
    echo ""
    echo "Stopping services..."
    
    # Kill backend if running
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "Backend stopped"
    fi
    
    # Kill frontend if running
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "Frontend stopped"
    fi
    
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM to run cleanup
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if node_modules exists in frontend
if [ ! -d "frontend/node_modules" ]; then
    echo "Error: Frontend dependencies not found. Please install them first:"
    echo "  cd frontend && npm install"
    exit 1
fi

# Function to kill process on a specific port
kill_port() {
    local port=$1
    local service_name=$2
    
    local pid=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "Port $port is already in use (PID: $pid). Killing process..."
        kill -9 $pid 2>/dev/null
        sleep 1
        # Check if it's still running
        if lsof -ti :$port > /dev/null 2>&1; then
            echo "Warning: Could not kill process on port $port. Please kill it manually:"
            echo "  kill -9 $pid"
            exit 1
        fi
        echo "✓ Process killed successfully"
    fi
}

# Check and kill existing backend process
kill_port 8000 "Backend"

# Check and kill existing frontend process
kill_port 5173 "Frontend"

# Start backend in background
echo "Starting backend on http://localhost:8000..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "Error: Backend failed to start. Check backend.log for details."
    echo "--- Backend Log ---"
    cat backend.log
    echo "-------------------"
    exit 1
fi

echo "✓ Backend is running (PID: $BACKEND_PID)"
echo "  API docs: http://localhost:8000/docs"
echo ""

# Start frontend in background
echo "Starting frontend on http://localhost:5173..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

# Check if frontend started successfully
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "Error: Frontend failed to start. Check frontend.log for details."
    cat frontend.log
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✓ Frontend is running (PID: $FRONTEND_PID)"
echo ""
echo "======================================"
echo "Application is running!"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "======================================"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
