#!/usr/bin/env python3

# Financial Email Transcription - One-Click Launcher
# Double-click this file to start the application!

import sys
import os

# Add current directory to path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
os.chdir(current_dir)

try:
    # Try to import and run the GUI directly
    import tkinter as tk
    print("✅ tkinter available - launching GUI directly...")
    
    # Import and run the GUI
    from financial_transcribe_gui import main
    main()
    
except ImportError as e:
    # tkinter not available, use the universal launcher
    print(f"⚠️  Direct launch failed: {e}")
    print("🔄 Falling back to universal launcher...")
    
    import subprocess
    
    # Try to run the universal launcher
    try:
        result = subprocess.run([sys.executable, 'launch_universal.py'])
        sys.exit(result.returncode)
    except Exception as launcher_error:
        print(f"❌ Universal launcher failed: {launcher_error}")
        print("\n🔧 Manual troubleshooting steps:")
        print("1. Ensure Python 3 is installed")
        print("2. Run: python3 financial_transcribe_gui.py")
        print("3. Check that all files are in the same folder")
        
        input("\nPress Enter to exit...")
        sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("\n🔧 Try running: python3 financial_transcribe_gui.py")
    input("\nPress Enter to exit...")
    sys.exit(1)