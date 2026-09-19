import os
import sys
import time
import socket
import threading
import urllib.request
import webbrowser
import subprocess

# Set working directory to executable or script directory
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    RUN_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RUN_DIR = BASE_DIR

os.chdir(RUN_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

HOST = "0.0.0.0"
LOCAL_HOST = "127.0.0.1"
PORT = 8000

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((LOCAL_HOST, port)) == 0

def find_available_port(start_port: int = 8000) -> int:
    port = start_port
    while port < start_port + 50:
        if not is_port_in_use(port):
            return port
        port += 1
    return start_port

def run_server(port: int):
    import uvicorn
    from backend.app.main import app
    
    # Configure uvicorn server
    config = uvicorn.Config(
        app=app,
        host=HOST,
        port=port,
        log_level="warning",
        access_log=False,
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    server.run()

def wait_for_server(port: int, timeout: float = 15.0) -> bool:
    start_time = time.time()
    url = f"http://{LOCAL_HOST}:{port}/health"
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False

def open_app_window(target_url: str):
    # Method 1: Try pywebview for native embedded desktop window
    try:
        import webview
        icon_path = os.path.join(BASE_DIR, "app_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(RUN_DIR, "app_icon.ico")
            
        window = webview.create_window(
            title="Arohan — Institute Student Development Platform",
            url=target_url,
            width=1320,
            height=860,
            min_size=(960, 640),
            confirm_close=False
        )
        webview.start(debug=False)
        return
    except Exception as e:
        print(f"pywebview window initialization skipped: {e}")

    # Method 2: Try Microsoft Edge App Mode (Chromeless standalone native-feeling window)
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for edge_exe in edge_paths:
        if os.path.exists(edge_exe):
            try:
                proc = subprocess.Popen([edge_exe, f"--app={target_url}", "--start-maximized"])
                proc.wait()
                return
            except Exception:
                pass

    # Method 3: System default browser
    webbrowser.open(target_url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def main():
    # Freeze support for Windows multiprocessing if needed
    import multiprocessing
    multiprocessing.freeze_support()

    global PORT
    # Use 8000 if available or find next
    if is_port_in_use(PORT):
        # Check if it's already our healthy server
        if wait_for_server(PORT, timeout=1.0):
            print(f"Server already running on port {PORT}, launching window...")
            open_app_window(f"http://{LOCAL_HOST}:{PORT}")
            return
        else:
            PORT = find_available_port(8001)

    # Start FastAPI server in background thread
    server_thread = threading.Thread(target=run_server, args=(PORT,), daemon=True)
    server_thread.start()

    # Wait for server ready
    if not wait_for_server(PORT, timeout=20.0):
        print("Warning: Server took longer to respond. Opening window now...")

    target_url = f"http://{LOCAL_HOST}:{PORT}"
    print(f"Arohan ISDP Platform ready at {target_url}")
    open_app_window(target_url)

if __name__ == "__main__":
    main()
