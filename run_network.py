"""
Run the OurHome app on your local network so any device on the same WiFi can access it.

Usage:
    python run_network.py

Then open the printed link (e.g., http://192.168.1.5:5000) on your phone, tablet, or other laptop.
"""
import socket
from ourhome_app import app, initialize_database


def get_local_ip():
    """Get the local IP address of this machine on the network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    with app.app_context():
        initialize_database()

    host = "0.0.0.0"
    port = 5000
    local_ip = get_local_ip()

    print("=" * 50)
    print("  OurHome is running on your local network!")
    print("=" * 50)
    print(f"  Local URL:   http://127.0.0.1:{port}")
    print(f"  Network URL: http://{local_ip}:{port}")
    print("=" * 50)
    print("  Open the Network URL on any device connected")
    print("  to the same WiFi / router.")
    print("=" * 50)

    app.run(host=host, port=port, debug=False, use_reloader=False)

