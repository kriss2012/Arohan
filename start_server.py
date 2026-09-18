import os
import sys
import time
import socket
import threading
import webbrowser
import urllib.request

# Ensure we are in the project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def wait_for_server(port: int = 8000, timeout: float = 10.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False

def open_browser(port: int = 8000):
    if wait_for_server(port):
        webbrowser.open(f"http://localhost:{port}")
    else:
        webbrowser.open(f"http://localhost:{port}")

def main():
    port = int(os.getenv("PORT", 8000))
    local_ip = get_local_ip()
    
    print("\n" + "=" * 68)
    print("  AROHAN ISDP — INSTITUTIONAL LOCAL SERVER")
    print("  Institute of Management Research and Development, Shirpur")
    print("=" * 68)
    print(f"\n  [OK] Server running on 0.0.0.0:{port}")
    print(f"  -> Local Computer:    http://localhost:{port}")
    print(f"  -> Campus LAN/Wi-Fi:  http://{local_ip}:{port}  (Students & Faculty)")
    print(f"  -> Interactive Docs:  http://localhost:{port}/docs")
    print(f"  -> Health Check:      http://localhost:{port}/health")
    print("\n" + "=" * 68)
    print("  Press Ctrl+C to stop the server.")
    print("=" * 68 + "\n")

    # Open browser in a separate thread once server is ready
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    import uvicorn
    from backend.app.main import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
