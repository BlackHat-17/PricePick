#!/usr/bin/env python3
"""
Setup script for PricePick backend
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        print(f"Full error output: {e.output}")
        return False
    except PermissionError as e:
        print(f"❌ {description} failed due to permission error: {e}\n")
        print("🔒 Please run this script as Administrator or check your folder permissions.")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up PricePick Backend...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Does venv folder exist? {os.path.exists('venv')}")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Create virtual environment using venv module directly
    if not os.path.exists("venv"):
        print("🔄 Creating virtual environment...")
        try:
            import venv
            venv.create("venv", with_pip=True)
            print("✅ Virtual environment created successfully")
        except Exception as e:
            print(f"❌ Creating virtual environment failed: {e}")
            print("🔒 Please run this script as Administrator or check your folder permissions.")
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists")
    
    # Determine venv python executable
    if os.name == 'nt':  # Windows
        venv_python = os.path.join('venv', 'Scripts', 'python.exe')
        activate_script = "venv\\Scripts\\activate"
    else:
        venv_python = os.path.join('venv', 'bin', 'python')
        activate_script = "source venv/bin/activate"

    # Upgrade pip using venv python
    if not run_command(f'"{venv_python}" -m pip install --upgrade pip', "Upgrading pip"):
        sys.exit(1)

    # Install dependencies using venv python
    if not run_command(f'"{venv_python}" -m pip install -r requirements.txt', "Installing dependencies"):
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            shutil.copy("env.example", ".env")
            print("✅ Created .env file from env.example")
        else:
            print("⚠️  env.example not found, you'll need to create .env manually")
    else:
        print("✅ .env file already exists")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Start the server:")
    print("   .python main.py")
    print("3. Open your browser to: http://localhost:8000")
    print("4. View API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
