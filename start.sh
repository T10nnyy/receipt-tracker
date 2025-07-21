#!/bin/bash
set -e

# Set default port if not provided
PORT=${PORT:-8501}

# Validate that PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Error: PORT must be a number, got: '$PORT'"
    echo "Using default port 8501"
    PORT=8501
fi

# Print debug information
echo "Starting Receipt Processor on port $PORT"
echo "Environment variables:"
echo "PORT=$PORT"

# Unset conflicting environment variables
unset STREAMLIT_SERVER_PORT

# Start streamlit directly
exec streamlit run src/app.py \
    --server.port "$PORT" \
    --server.address "0.0.0.0" \
    --server.headless true \
    --browser.gatherUsageStats false
