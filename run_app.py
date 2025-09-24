#!/usr/bin/env python3
"""
Financial Audio Transcription Suite - Launcher
Double-click to start the GUI application
"""

import sys
import os

def main():
    """Launch the Financial Audio Transcription GUI"""
    try:
        # Import and run the GUI
        from financial_transcribe_gui import main as gui_main
        gui_main()
    except ImportError as e:
        print("=" * 50)
        print("FINANCIAL AUDIO TRANSCRIPTION SUITE")
        print("=" * 50)
        print(f"Import Error: {e}")
        print("\nRequired packages not found.")
        print("Please install required packages:")
        print("  pip install tkinter openai python-dotenv requests yt-dlp")
        print("=" * 50)
        input("Press Enter to exit...")
    except Exception as e:
        print("=" * 50)
        print("FINANCIAL AUDIO TRANSCRIPTION SUITE")
        print("=" * 50)
        print(f"Error: {e}")
        print("\nThe application encountered an error.")
        print("Please check your configuration and try again.")
        print("=" * 50)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()