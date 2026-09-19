import os
import sys
import time
import socket
import threading
import webbrowser
import urllib.request

# Configure UTF-8 with fallback if supported by Python runtime
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure we are in the project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def get_network_ips() -> list[str]:
    """Discover all reachable local network IPv4 addresses (Wi-Fi, Ethernet)."""
    ips = set()
    # Method 1: Connect to public DNS without sending data to identify outbound adapter
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and not primary_ip.startswith("127."):
            ips.add(primary_ip)
    except Exception:
        pass

    # Method 2: Inspect host name addresses
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and ":" not in ip:
                ips.add(ip)
    except Exception:
        pass

    # Method 3: Fallback
    if not ips:
        ips.add("127.0.0.1")

    return sorted(list(ips))

def wait_for_server(port: int = 8000, timeout: float = 12.0) -> bool:
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
    wait_for_server(port)
    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

def main():
    port = int(os.getenv("PORT", 8000))
    network_ips = get_network_ips()
    
    print("\n" + "=" * 70)
    print("  AROHAN ISDP -- CAMPUS LMS & INSTITUTIONAL PLATFORM")
    print("  RC Patel Educational Trust's IMRD, Shirpur")
    print("=" * 70)
    print(f"\n  [SUCCESS] Server running on 0.0.0.0:{port} (All Network Interfaces)")
    print("\n  [LOCAL COMPUTER]")
    print(f"  -> Open in Browser:       http://localhost:{port}")
    print("\n  [ANY DEVICE ON CAMPUS WI-FI / LAN (Mobiles, Tablets, Laptops)]")
    for ip in network_ips:
        print(f"  -> Connect on Wi-Fi:      http://{ip}:{port}")
    print("\n  [API & HEALTH]")
    print(f"  -> Interactive Docs:      http://localhost:{port}/docs")
    print(f"  -> System Health Check:   http://localhost:{port}/health")
    print("\n" + "-" * 70)
    print("  DEFAULT DEMO CREDENTIALS (Instant Login):")
    print("  * Student:        student1@imrd.ac.in   / Student@123")
    print("  * Faculty:        faculty1@imrd.ac.in   / Faculty@123")
    print("  * Controller:     controller@imrd.ac.in / Exam@123")
    print("  * Admin:          admin@imrd.ac.in      / Admin@123")
    print("=" * 70)
    print("  Press Ctrl+C to stop the server.\n")

    # Open browser in a separate thread once server is ready
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    import uvicorn
    from backend.app.main import app

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n[INFO] Arohan ISDP Server stopped safely. Goodbye!")
    except Exception as e:
        print(f"\n[ERROR] Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
