#!/bin/bash

# Financial Email Transcription Service Startup Script
# This script runs the email transcription service with automatic restart

SCRIPT_DIR="/workspaces/codespaces-blank"
PYTHON_SCRIPT="email_transcribe_financial.py"
LOG_FILE="$SCRIPT_DIR/transcribe_service.log"
PID_FILE="$SCRIPT_DIR/transcribe_service.pid"

cd "$SCRIPT_DIR" || exit 1

echo "$(date): Starting Financial Email Transcription Service" >> "$LOG_FILE"

# Function to clean up on exit
cleanup() {
    echo "$(date): Service stopped" >> "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Store PID
echo $$ > "$PID_FILE"

# Main loop with automatic restart
while true; do
    echo "$(date): Starting email transcription..." >> "$LOG_FILE"
    
    # Run the Python script
    python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1
    
    # If script exits, log it and restart after delay
    exit_code=$?
    echo "$(date): Script exited with code $exit_code. Restarting in 30 seconds..." >> "$LOG_FILE"
    
    # Wait before restart
    sleep 30
done