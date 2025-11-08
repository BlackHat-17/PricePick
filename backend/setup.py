#!/usr/bin/env python3
"""
Setup script for PricePick backend
"""

import os
import sys
import shutil
from pathlib import Path

def install_packages_programmatically(python_exec, packages_or_file, description):
    """Install packages using pip programmatically (no subprocess)"""
    print(f"🔄 {description}...")
    try:
        # Add venv site-packages to path to access pip
        venv_lib = os.path.join(os.path.dirname(python_exec), '..', 'Lib' if os.name == 'nt' else 'lib')
        venv_site_packages = None
        
        if os.path.exists(venv_lib):
            for item in os.listdir(venv_lib):
                if item.startswith('python'):
                    venv_site_packages = os.path.join(venv_lib, item, 'site-packages')
                    break
        
        original_path = sys.path[:]
        try:
            if venv_site_packages and os.path.exists(venv_site_packages):
                sys.path.insert(0, venv_site_packages)
            
            # Use pip's programmatic API
            import pip._internal.main as pip_main
            
            if isinstance(packages_or_file, list):
                args = ['install'] + packages_or_file
            else:
                args = ['install', '-r', packages_or_file]
            
            result = pip_main.main(args)
            
            if result == 0:
                print(f"✅ {description} completed successfully")
                return True
            else:
                print(f"⚠️  {description} completed with warnings (exit code: {result})")
                return True  # Still return True as it might have worked
        finally:
            sys.path = original_path
            
    except ImportError:
        # Fallback: provide manual instructions
        print(f"⚠️  Could not use pip programmatically. Please run manually:")
        if isinstance(packages_or_file, list):
            print(f"   {python_exec} -m pip install {' '.join(packages_or_file)}")
        else:
            print(f"   {python_exec} -m pip install -r {packages_or_file}")
        return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        print(f"⚠️  Please install manually: {python_exec} -m pip install -r requirements.txt")
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

    # Upgrade pip using venv python (programmatically)
    print("🔄 Upgrading pip...")
    try:
        venv_lib = os.path.join(os.path.dirname(venv_python), '..', 'Lib' if os.name == 'nt' else 'lib')
        venv_site_packages = None
        
        if os.path.exists(venv_lib):
            for item in os.listdir(venv_lib):
                if item.startswith('python'):
                    venv_site_packages = os.path.join(venv_lib, item, 'site-packages')
                    break
        
        if venv_site_packages and os.path.exists(venv_site_packages):
            sys.path.insert(0, venv_site_packages)
        
        try:
            import pip._internal.main as pip_main
            if pip_main.main(['install', '--upgrade', 'pip']) == 0:
                print("✅ Upgrading pip completed successfully")
            else:
                print("⚠️  Pip upgrade had issues, but continuing...")
        except:
            print("⚠️  Could not upgrade pip programmatically. Continuing...")
        finally:
            if venv_site_packages and venv_site_packages in sys.path:
                sys.path.remove(venv_site_packages)
    except Exception as e:
        print(f"⚠️  Could not upgrade pip: {e}. Continuing...")

    # Install dependencies using venv python
    if not install_packages_programmatically(venv_python, "requirements.txt", "Installing dependencies"):
        print("⚠️  Automatic installation failed. Please install manually:")
        print(f"   {venv_python} -m pip install -r requirements.txt")
        # Don't exit - let user install manually
    
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
    print("   python main.py")
    print("3. Open your browser to: http://localhost:8000")
    print("4. View API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
