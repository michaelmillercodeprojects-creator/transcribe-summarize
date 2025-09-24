#!/bin/bash

# Stop the Financial Email Transcription Service

SCRIPT_DIR="/workspaces/codespaces-blank"
PID_FILE="$SCRIPT_DIR/transcribe_service.pid"
LOG_FILE="$SCRIPT_DIR/transcribe_service.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "$(date): Stopping service (PID: $PID)" >> "$LOG_FILE"
    
    # Try graceful shutdown first
    kill -TERM "$PID" 2>/dev/null
    sleep 5
    
    # Force kill if still running
    if kill -0 "$PID" 2>/dev/null; then
        echo "$(date): Force stopping service" >> "$LOG_FILE"
        kill -KILL "$PID" 2>/dev/null
    fi
    
    # Also kill any Python processes running the script
    pkill -f "email_transcribe_financial.py" 2>/dev/null
    
    rm -f "$PID_FILE"
    echo "Service stopped"
else
    echo "Service is not running (no PID file found)"
fi