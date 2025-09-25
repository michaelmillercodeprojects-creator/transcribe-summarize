#!/usr/bin/env python3
"""
Cross-platform installer for Financial Transcription Tool
This script will install all required dependencies.
"""

import sys
import subprocess
import os
import platform

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} detected.")
        print("🔥 Python 3.8 or higher is required.")
        print("\nPlease install a newer version of Python:")
        print("https://www.python.org/downloads/")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    return True

def install_requirements():
    """Install requirements using pip"""
    try:
        print("\n📦 Upgrading pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--user"])
        
        print("\n📥 Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--user"])
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Installation failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Try running as administrator/sudo")
        print("3. Make sure you have development tools installed:")
        
        system = platform.system().lower()
        if system == "windows":
            print("   - Install Microsoft C++ Build Tools")
        elif system == "darwin":
            print("   - Run: xcode-select --install")
        else:
            print("   - Ubuntu/Debian: sudo apt install build-essential python3-dev")
            print("   - CentOS/RHEL: sudo yum groupinstall 'Development Tools'")
        
        return False

def check_env_file():
    """Check if .env file exists and remind user about API key"""
    if not os.path.exists(".env"):
        print("\n⚠️  .env file not found!")
        print("\n🔑 You need to create a .env file with your OpenAI API key:")
        print("1. Create a file named '.env' in this folder")
        print("2. Add this line: OPENAI_API_KEY=your_api_key_here")
        print("3. Replace 'your_api_key_here' with your actual OpenAI API key")
        print("\n🌐 Get your API key from: https://platform.openai.com/api-keys")
    else:
        print("\n✅ .env file found")

def main():
    print("==========================================")
    print("🎵 Financial Transcription Tool Installer")
    print("==========================================")
    print(f"\n🖥️  Platform: {platform.system()} {platform.release()}")
    
    if not check_python_version():
        input("\nPress Enter to exit...")
        return False
    
    if not install_requirements():
        input("\nPress Enter to exit...")
        return False
    
    check_env_file()
    
    print("\n🎉 ==========================================")
    print("✅ Installation Complete!")
    print("==========================================")
    print("\n🚀 You can now run the application:")
    print(f"   python{'' if platform.system() == 'Windows' else '3'} run_app.py")
    print("\n📁 Or double-click 'run_app.py' if your system supports it")
    
    input("\nPress Enter to exit...")
    return True

if __name__ == "__main__":
    main()