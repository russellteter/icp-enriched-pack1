#!/bin/bash

# Create required directories
mkdir -p runs/latest cache exports

# Start the server with dynamic port
python -m uvicorn src.server.app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2