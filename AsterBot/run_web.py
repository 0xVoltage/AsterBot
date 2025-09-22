#!/usr/bin/env python3
"""
Script to run AsterBot web interface
"""

import sys
import os
import threading
import time
import webbrowser
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web.app import app, socketio

def open_browser():
    """Open browser after 2 seconds"""
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:5000')
        print("Web page opened automatically!")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print("Access manually: http://localhost:5000")

if __name__ == '__main__':
    print("Starting AsterBot Web Interface...")
    print("URL: http://localhost:5000")
    print("Opening browser automatically...")
    print("Use Ctrl+C to stop")
    print()

    # Iniciar thread para abrir navegador
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Web interface stopped.")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")