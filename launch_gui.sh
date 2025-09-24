#!/bin/bash

# Financial Email Transcription - Easy Launcher
# This script launches the GUI application and finds Python automatically

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Financial Email Transcription GUI..."
echo "==============================================="

# Function to find Python executable
find_python() {
    local python_cmd=""
    
    # Common Python locations to check
    local python_paths=(
        "python3"
        "python"
        "/usr/bin/python3"
        "/usr/bin/python"
        "/usr/local/bin/python3"
        "/usr/local/bin/python"
        "/opt/python/bin/python3"
        "/opt/python/bin/python"
        "$HOME/.pyenv/shims/python3"
        "$HOME/.pyenv/shims/python"
        "/home/codespace/.python/current/bin/python"
        "/home/codespace/.python/current/bin/python3"
        "$(which python3 2>/dev/null)"
        "$(which python 2>/dev/null)"
    )
    
    # Check conda/mamba environments
    if command -v conda &> /dev/null; then
        python_paths+=("$(conda info --base)/bin/python")
        python_paths+=("$(conda info --base)/bin/python3")
    fi
    
    # Check virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        python_paths+=("$VIRTUAL_ENV/bin/python")
        python_paths+=("$VIRTUAL_ENV/bin/python3")
    fi
    
    # Try each Python path
    for path in "${python_paths[@]}"; do
        if [ -n "$path" ] && [ -x "$path" ]; then
            # Check if it's Python 3
            if "$path" -c "import sys; exit(0 if sys.version_info[0] >= 3 else 1)" 2>/dev/null; then
                echo "Found Python 3 at: $path"
                python_cmd="$path"
                break
            fi
        fi
    done
    
    echo "$python_cmd"
}

# Find Python executable
PYTHON_CMD=$(find_python)

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Error: Could not find Python 3 installation"
    echo ""
    echo "Please install Python 3 from one of these sources:"
    echo "  • Official Python: https://www.python.org/downloads/"
    echo "  • Anaconda: https://www.anaconda.com/products/distribution"
    echo "  • System package manager:"
    echo "    - Ubuntu/Debian: sudo apt install python3"
    echo "    - CentOS/RHEL: sudo yum install python3"
    echo "    - macOS: brew install python3"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if GUI script exists
if [ ! -f "financial_transcribe_gui.py" ]; then
    echo "❌ Error: financial_transcribe_gui.py not found"
    echo "Please ensure all files are in the correct location: $SCRIPT_DIR"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check tkinter availability
echo "Checking GUI dependencies..."
if ! "$PYTHON_CMD" -c "import tkinter" 2>/dev/null; then
    echo "❌ Error: tkinter (GUI library) is not available"
    echo ""
    echo "Please install tkinter:"
    echo "  • Ubuntu/Debian: sudo apt install python3-tk"
    echo "  • CentOS/RHEL: sudo yum install tkinter"
    echo "  • macOS: Should be included with Python"
    echo "  • Windows: Should be included with Python"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Launch the GUI application
echo "✅ All dependencies found"
echo "🚀 Launching GUI application..."
echo ""

"$PYTHON_CMD" financial_transcribe_gui.py

echo ""
echo "Application closed."
read -p "Press Enter to exit..."