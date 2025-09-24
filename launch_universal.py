#!/usr/bin/env python3
"""
Universal Launcher for Financial Email Transcription GUI
This script finds Python and launches the GUI even if Python is not in PATH
"""

import sys
import os
import subprocess
import platform

def find_python():
    """Find a suitable Python 3 executable"""
    
    # Common Python commands to try
    python_commands = ['python3', 'python']
    
    # Platform-specific paths
    if platform.system() == "Windows":
        # Windows-specific paths
        python_paths = [
            r'C:\Python39\python.exe',
            r'C:\Python310\python.exe', 
            r'C:\Python311\python.exe',
            r'C:\Python312\python.exe',
            r'C:\Users\{}\AppData\Local\Programs\Python\Python39\python.exe'.format(os.getenv('USERNAME', '')),
            r'C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe'.format(os.getenv('USERNAME', '')),
            r'C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe'.format(os.getenv('USERNAME', '')),
            r'C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe'.format(os.getenv('USERNAME', '')),
            r'C:\ProgramData\Anaconda3\python.exe',
            r'C:\Users\{}\Anaconda3\python.exe'.format(os.getenv('USERNAME', '')),
            r'C:\Users\{}\Miniconda3\python.exe'.format(os.getenv('USERNAME', '')),
        ]
        
        # Try Windows Python Launcher first
        try:
            result = subprocess.run(['py', '-3', '--version'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return 'py -3'
        except:
            pass
            
    else:
        # Unix-like systems (Linux, macOS)
        python_paths = [
            '/usr/bin/python3',
            '/usr/bin/python',
            '/usr/local/bin/python3',
            '/usr/local/bin/python',
            '/opt/python/bin/python3',
            '/opt/python/bin/python',
            os.path.expanduser('~/.pyenv/shims/python3'),
            os.path.expanduser('~/.pyenv/shims/python'),
            '/home/codespace/.python/current/bin/python',
            '/home/codespace/.python/current/bin/python3',
        ]
        
        # Add conda paths if available
        try:
            conda_base = subprocess.check_output(['conda', 'info', '--base'], 
                                               text=True, timeout=5).strip()
            python_paths.extend([
                os.path.join(conda_base, 'bin', 'python'),
                os.path.join(conda_base, 'bin', 'python3')
            ])
        except:
            pass
        
        # Add virtual environment if active
        venv = os.getenv('VIRTUAL_ENV')
        if venv:
            python_paths.extend([
                os.path.join(venv, 'bin', 'python'),
                os.path.join(venv, 'bin', 'python3')
            ])
    
    # Try commands first (in PATH)
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                # Check if it's Python 3
                try:
                    version_check = subprocess.run([cmd, '-c', 
                        'import sys; exit(0 if sys.version_info[0] >= 3 else 1)'],
                        capture_output=True, timeout=5)
                    if version_check.returncode == 0:
                        return cmd
                except:
                    continue
        except:
            continue
    
    # Try specific paths
    for path in python_paths:
        if path and os.path.isfile(path):
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    # Check if it's Python 3
                    try:
                        version_check = subprocess.run([path, '-c', 
                            'import sys; exit(0 if sys.version_info[0] >= 3 else 1)'],
                            capture_output=True, timeout=5)
                        if version_check.returncode == 0:
                            return path
                    except:
                        continue
            except:
                continue
    
    return None

def check_tkinter(python_cmd):
    """Check if tkinter is available"""
    try:
        if isinstance(python_cmd, str) and ' ' in python_cmd:
            # Handle "py -3" case
            cmd_parts = python_cmd.split()
        else:
            cmd_parts = [python_cmd]
        
        result = subprocess.run(cmd_parts + ['-c', 'import tkinter'], 
                              capture_output=True, timeout=10)
        return result.returncode == 0
    except:
        return False

def main():
    """Main launcher function"""
    print("Financial Email Transcription - Universal Launcher")
    print("=" * 50)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Find Python
    print("🔍 Searching for Python 3...")
    python_cmd = find_python()
    
    if not python_cmd:
        print("❌ Error: Could not find Python 3 installation")
        print("\nPlease install Python 3 from:")
        print("  • https://www.python.org/downloads/")
        print("  • https://www.anaconda.com/products/distribution")
        print("\nOr use your system package manager:")
        if platform.system() == "Linux":
            print("  • Ubuntu/Debian: sudo apt install python3")
            print("  • CentOS/RHEL: sudo yum install python3")
        elif platform.system() == "Darwin":
            print("  • macOS: brew install python3")
        
        input("\nPress Enter to exit...")
        return 1
    
    print(f"✅ Found Python 3: {python_cmd}")
    
    # Check if GUI script exists
    gui_script = "financial_transcribe_gui.py"
    if not os.path.isfile(gui_script):
        print(f"❌ Error: {gui_script} not found")
        print(f"Current directory: {script_dir}")
        input("\nPress Enter to exit...")
        return 1
    
    # Check tkinter
    print("🔍 Checking GUI dependencies...")
    if not check_tkinter(python_cmd):
        print("❌ Error: tkinter (GUI library) is not available")
        print("\nPlease install tkinter:")
        if platform.system() == "Linux":
            print("  • Ubuntu/Debian: sudo apt install python3-tk")
            print("  • CentOS/RHEL: sudo yum install tkinter")
        elif platform.system() == "Darwin":
            print("  • macOS: Should be included with Python")
        elif platform.system() == "Windows":
            print("  • Windows: Should be included with Python")
            print("  • Try reinstalling Python with 'tcl/tk' option checked")
        
        input("\nPress Enter to exit...")
        return 1
    
    print("✅ All dependencies found")
    print("🚀 Launching GUI application...")
    print()
    
    # Launch the GUI
    try:
        if isinstance(python_cmd, str) and ' ' in python_cmd:
            # Handle "py -3" case
            cmd_parts = python_cmd.split() + [gui_script]
        else:
            cmd_parts = [python_cmd, gui_script]
        
        # Launch and wait
        result = subprocess.run(cmd_parts)
        
        print("\nApplication closed.")
        if platform.system() == "Windows":
            input("Press Enter to exit...")
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        input("\nPress Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())