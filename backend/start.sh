#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "Starting SMU-Bab local backend..."
echo "API docs: http://127.0.0.1:8000/docs"
echo "Health:   http://127.0.0.1:8000/api/health"
echo ""

uvicorn main:app --host 127.0.0.1 --port 8000 --reload
