#!/bin/bash
echo "Starting FastAPI server locally for testing..."
cd /c/Users/TLCOM/Desktop/claude/real-estate-platform/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload