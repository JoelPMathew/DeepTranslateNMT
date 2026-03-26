#!/usr/bin/env python
"""
Simple startup script for DeepTranslate Pro 2.0 API
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    try:
        import uvicorn
        from enhanced_api import app
        
        print("=" * 60)
        print("[*] DeepTranslate Pro 2.0 - API Server")
        print("=" * 60)
        print("Starting server on http://127.0.0.1:6000")
        print("Press Ctrl+C to stop\n")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=6000,
            reload=False,  # Disable reload to avoid issues on Windows
            log_level="info"
        )
    except Exception as e:
        print(f"[ERROR] Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
