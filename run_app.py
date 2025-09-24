#!/usr/bin/env python3
"""
Financial Email Transcription - Simple Launcher
Double-click to start the GUI application
"""

try:
    # Import and run the GUI directly
    from financial_transcribe_gui import main
    main()
except ImportError as e:
    print(f"Error: {e}")
    print("Please install: pip install tkinter")
    input("Press Enter to exit...")
except Exception as e:
    print(f"Error: {e}")
    input("Press Enter to exit...")