#!/bin/bash
set -e

# Kill any existing services on these ports
echo "Stopping existing services..."
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
fuser -k 8002/tcp 2>/dev/null || true

# Start Backend (Port 8000)
echo "Starting Backend on PORT 8000..."
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Inference Service (Port 8002)
echo "Starting Inference Service on PORT 8002..."
cd inference
../.venv/bin/python main.py &
INFERENCE_PID=$!
cd ..

# Start Frontend (Port 3000)
echo "Starting Frontend on PORT 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "All services started!"
echo "Backend PID: $BACKEND_PID"
echo "Inference PID: $INFERENCE_PID"
echo "Frontend PID: $FRONTEND_PID"

# Wait for user input to kill everything on exit
read -p "Press Enter to stop all services..."
kill $BACKEND_PID $INFERENCE_PID $FRONTEND_PID
