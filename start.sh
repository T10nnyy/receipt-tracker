#!/bin/bash

# Set default port if not provided
export PORT=${PORT:-8501}

# Print debug information
echo "Starting Receipt Processor on port $PORT"
echo "Environment variables:"
echo "PORT=$PORT"
echo "STREAMLIT_SERVER_PORT=$STREAMLIT_SERVER_PORT"

# Start streamlit directly
streamlit run src/app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
