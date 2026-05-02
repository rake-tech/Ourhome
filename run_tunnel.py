"""
Run the OurHome app and create a public HTTPS link using Cloudflare Tunnel.
Anyone in the world can open this link — even on mobile data.

Requirements:
    pip install pyngrok
    # OR use cloudflared (see below)

Usage:
    python run_tunnel.py
"""
import subprocess
import sys
import time
import urllib.request

from ourhome_app import app, initialize_database


def check_module(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def install_module(module_name):
    print(f"Installing {module_name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])


def get_public_url_ngrok(port):
    from pyngrok import ngrok
    tunnel = ngrok.connect(port, "http")
    return tunnel.public_url


def get_public_url_cloudflared(port):
    """Use cloudflared (free, no account needed)."""
    import atexit
    import os
    import platform

    system = platform.system().lower()
    if system == "windows":
        exe = "cloudflared.exe"
    else:
        exe = "cloudflared"

    # Try to find cloudflared in PATH
    cloudflared_path = None
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, exe)
        if os.path.isfile(candidate):
            cloudflared_path = candidate
            break

    if cloudflared_path is None:
        print("cloudflared not found in PATH.")
        print("Download it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        print("Or use ngrok instead (pip install pyngrok).")
        return None

    proc = subprocess.Popen(
        [cloudflared_path, "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    atexit.register(proc.terminate)

    # Parse output to find the public URL
    url = None
    for _ in range(60):  # Wait up to 60 seconds
        line = proc.stdout.readline()
        if line:
            print(line.strip())
            if "https://" in line and ".trycloudflare.com" in line:
                parts = line.split()
                for part in parts:
                    if part.startswith("https://") and ".trycloudflare.com" in part:
                        url = part.strip()
                        break
            if url:
                break
        time.sleep(0.5)

    return url


def main():
    port = 5000

    with app.app_context():
        initialize_database()

    # Start Flask in a background thread so we can print the link
    from threading import Thread
    server = Thread(target=lambda: app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False))
    server.daemon = True
    server.start()

    # Wait a moment for the server to start
    time.sleep(1)
    for _ in range(10):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}")
            break
        except Exception:
            time.sleep(0.5)

    print("=" * 60)
    print("  Creating a public link for OurHome...")
    print("=" * 60)

    public_url = None

    # Try cloudflared first (free, no signup)
    try:
        public_url = get_public_url_cloudflared(port)
    except Exception as e:
        print(f"cloudflared failed: {e}")

    # Fallback to ngrok
    if not public_url:
        if not check_module("pyngrok"):
            install_module("pyngrok")
        try:
            public_url = get_public_url_ngrok(port)
        except Exception as e:
            print(f"ngrok failed: {e}")

    print("=" * 60)
    if public_url:
        print("  Your public link is ready!")
        print(f"  {public_url}")
        print("=" * 60)
        print("  Share this link with anyone — it works on any device.")
        print("  Press CTRL+C to stop the server.")
        print("=" * 60)
    else:
        print("  Could not create a public link.")
        print("  Try running: python run_network.py")
        print("  (works on same WiFi only)")
        print("=" * 60)
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()

