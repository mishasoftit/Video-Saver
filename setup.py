#!/usr/bin/env python3
"""
Setup script for Telegram Video Downloader Bot
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print setup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🎬 Telegram Video Downloader Bot Setup 🎬            ║
║                                                              ║
║  This script will help you set up the bot quickly           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("🎵 Checking FFmpeg installation...")
    
    if shutil.which('ffmpeg'):
        print("✅ FFmpeg is installed")
        return True
    else:
        print("⚠️  FFmpeg not found")
        print("   Audio extraction may not work properly")
        print("   Please install FFmpeg:")
        print("   - Windows: Download from https://ffmpeg.org/download.html")
        print("   - Linux: sudo apt install ffmpeg")
        print("   - macOS: brew install ffmpeg")
        return False

def create_virtual_environment():
    """Create virtual environment"""
    print("📦 Creating virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("📚 Installing dependencies...")
    
    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = Path("venv/Scripts/pip")
    else:  # Linux/macOS
        pip_path = Path("venv/bin/pip")
    
    if not pip_path.exists():
        print("❌ Virtual environment pip not found")
        return False
    
    try:
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment_file():
    """Set up environment file"""
    print("⚙️  Setting up environment file...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    # Copy example to .env
    try:
        shutil.copy(env_example, env_file)
        print("✅ .env file created from template")
        print("📝 Please edit .env file and add your Telegram Bot Token")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ["downloads", "logs"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created {directory}/ directory")
            except Exception as e:
                print(f"❌ Failed to create {directory}/ directory: {e}")
                return False
        else:
            print(f"✅ {directory}/ directory already exists")
    
    return True

def get_bot_token():
    """Help user get bot token"""
    print("\n🤖 Getting Telegram Bot Token:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot command")
    print("3. Follow the instructions to create your bot")
    print("4. Copy the bot token")
    print("5. Edit the .env file and replace 'your_bot_token_here' with your actual token")
    
    input("\nPress Enter when you have your bot token ready...")

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your Telegram Bot Token")
    print("2. Activate virtual environment:")
    
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Linux/macOS
        print("   source venv/bin/activate")
    
    print("3. Run the bot:")
    print("   python main.py")
    print("\n🚀 Your bot will be ready to download videos!")

def main():
    """Main setup function"""
    print_banner()
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
    
    ffmpeg_available = check_ffmpeg()
    
    # Setup steps
    steps = [
        ("Creating virtual environment", create_virtual_environment),
        ("Installing dependencies", install_dependencies),
        ("Setting up environment file", setup_environment_file),
        ("Creating directories", create_directories),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ Setup failed at: {step_name}")
            sys.exit(1)
    
    # Help with bot token
    get_bot_token()
    
    # Print completion message
    print_next_steps()
    
    if not ffmpeg_available:
        print("\n⚠️  Warning: FFmpeg not found. Audio extraction may not work.")
        print("   Please install FFmpeg for full functionality.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)