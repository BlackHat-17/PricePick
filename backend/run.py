#!/usr/bin/env python3
"""
Simple run script for PricePick backend
Runs main.py directly without subprocess
"""

import os
import sys

def main():
    """Run the PricePick backend"""
    print("🚀 Starting PricePick Backend...")
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ main.py not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Add current directory to path to ensure imports work
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, backend_dir)
    os.chdir(backend_dir)
    
    # Import and run main module directly
    try:
        print("🔄 Starting server...")
        # Import main module to get the app and settings
        import main
        from config import settings
        import uvicorn
        
        # Run uvicorn directly (same as main.py's __main__ block)
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
