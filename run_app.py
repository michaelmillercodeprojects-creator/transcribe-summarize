#!/usr/bin/env python3
"""
Financial Email Transcription - One-Click Launcher
Double-click this file to start the application!
"""

import sys
import os

def main():
    # Change to script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    print("🚀 Financial Email Transcription - Starting GUI...")
    print("=" * 50)
    
    try:
        # Check if GUI file exists
        if not os.path.exists("financial_transcribe_gui.py"):
            print("❌ Error: financial_transcribe_gui.py not found")
            print(f"Current directory: {current_dir}")
            input("\nPress Enter to exit...")
            return 1
        
        # Try to import tkinter first
        try:
            import tkinter as tk
            print("✅ GUI libraries available")
        except ImportError as e:
            print(f"❌ GUI libraries not available: {e}")
            print("\n🔧 Please install tkinter:")
            print("• Ubuntu/Debian: sudo apt install python3-tk")
            print("• CentOS/RHEL: sudo yum install tkinter")
            print("• Windows/macOS: Usually included with Python")
            input("\nPress Enter to exit...")
            return 1
        
        # Import and run the GUI
        print("🎯 Launching GUI application...")
        
        # Add current directory to Python path
        sys.path.insert(0, current_dir)
        
        from financial_transcribe_gui import main as gui_main
        gui_main()
        
        return 0
        
    except ImportError as e:
        print(f"⚠️  Import error: {e}")
        print("🔄 Trying alternative launch method...")
        
        # Fallback to subprocess launch
        try:
            import subprocess
            result = subprocess.run([sys.executable, 'financial_transcribe_gui.py'])
            return result.returncode
        except Exception as subprocess_error:
            print(f"❌ Alternative launch failed: {subprocess_error}")
            print("\n🔧 Manual troubleshooting:")
            print("1. Ensure Python 3 is installed")
            print("2. Try: python3 financial_transcribe_gui.py")
            print("3. Check all files are in the same folder")
            input("\nPress Enter to exit...")
            return 1
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("\n🔧 Try manual launch: python3 financial_transcribe_gui.py")
        input("\nPress Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())