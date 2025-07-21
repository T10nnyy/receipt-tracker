#!/usr/bin/env python3
"""
Startup script for Railway deployment
"""
import os
import subprocess
import sys

def main():
    # Get port from environment variable
    port_str = os.environ.get("PORT", "8501")
    
    # Validate port
    try:
        port = int(port_str)
        if port <= 0 or port > 65535:
            raise ValueError("Port out of range")
    except (ValueError, TypeError):
        print(f"Error: Invalid PORT value '{port_str}', using default 8501")
        port = 8501
    
    # Clear conflicting environment variables
    env = os.environ.copy()
    env.pop('STREAMLIT_SERVER_PORT', None)
    
    # Print startup info
    print(f"Starting Streamlit app on port {port}")
    print(f"Working directory: {os.getcwd()}")
    
    # Build command
    cmd = [
        "streamlit",
        "run",
        "src/app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    # Execute streamlit
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
