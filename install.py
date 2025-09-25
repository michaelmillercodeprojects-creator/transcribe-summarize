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

def setup_env_file():
    """Create .env file and prompt for API key"""
    if os.path.exists(".env"):
        print("\n✅ .env file already exists")
        return
    
    print("\n🔑 Setting Up OpenAI API Key")
    print("=" * 40)
    print("\nYou need an OpenAI API key to use this tool.")
    print("🌐 Get one from: https://platform.openai.com/api-keys")
    print("\n💡 The key will be saved securely in a .env file")
    
    api_key = input("\nEnter your OpenAI API key (or press Enter to skip): ").strip()
    
    if api_key:
        try:
            with open(".env", "w") as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
            print("\n✅ API key saved to .env file!")
        except Exception as e:
            print(f"\n❌ Error saving .env file: {e}")
            print("You can create it manually later.")
    else:
        print("\n⚠️  No API key entered. You can add it later by:")
        print("1. Creating a .env file in this folder")
        print("2. Adding: OPENAI_API_KEY=your_key_here")
        print("3. Replacing 'your_key_here' with your actual API key")

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
    
    setup_env_file()
    
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