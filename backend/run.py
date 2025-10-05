#!/usr/bin/env python3
"""
Simple run script for PricePick backend
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the PricePick backend"""
    print("🚀 Starting PricePick Backend...")
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ main.py not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Check if virtual environment exists
    if not os.path.exists("venv"):
        print("❌ Virtual environment not found. Please run setup.py first.")
        sys.exit(1)
    
    # Determine Python executable
    if os.name == 'nt':  # Windows
        python_exec = "venv\\Scripts\\python"
    else:  # Unix/Linux/MacOS
        python_exec = "venv/bin/python"
    
    # Check if Python executable exists
    if not os.path.exists(python_exec):
        print(f"❌ Python executable not found at {python_exec}")
        sys.exit(1)
    
    # Run the application
    try:
        print("🔄 Starting server...")
        subprocess.run([python_exec, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
