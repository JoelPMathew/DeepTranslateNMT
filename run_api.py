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

        host = os.getenv("API_HOST", "127.0.0.1")
        port = int(os.getenv("API_PORT", "6000"))
        
        print("=" * 60)
        print("[*] DeepTranslate Pro 2.0 - API Server")
        print("=" * 60)
        print(f"Starting server on http://{host}:{port}")
        if port == 6000:
            print("[!] Note: Chrome extensions block port 6000 (ERR_UNSAFE_PORT).")
            print("[!] For extension use, run with API_PORT=8000.")
        print("Press Ctrl+C to stop\n")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,  # Disable reload to avoid issues on Windows
            log_level="info"
        )
    except Exception as e:
        print(f"[ERROR] Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
