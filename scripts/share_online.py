"""
================================================================================
SME FINANCE COPILOT — LIVE ONLINE SHARING RUNNER
================================================================================
Allows other users (mobile phones, colleagues, remote evaluators) to access
the SME Finance Copilot over the internet whenever your PC is online.

Features:
  1. Starts FastAPI / Uvicorn server bound to 0.0.0.0:8050.
  2. Generates an instant, secure public HTTPS tunnel using OpenSSH.
  3. Detects your Local Wi-Fi / LAN IP for devices on the same network.
  4. Automatically copies the Public URL to your Windows Clipboard.
  5. Automatically launches the login portal in your default browser.
  6. Provides graceful cleanup on exit (CTRL+C).
================================================================================
"""

import os
import sys
import re
import time
import socket
import signal
import subprocess
import threading
from pathlib import Path

# Configure Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PORT = 8050
APP_MODULE = "src.api.app:app"


def get_local_ip() -> str:
    """Detects the primary IPv4 address on the local Wi-Fi or LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def copy_to_clipboard(text: str) -> bool:
    """Copies the text to the Windows clipboard via clip.exe."""
    try:
        proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
        proc.communicate(input=text.encode("utf-8"))
        return True
    except Exception:
        return False


def start_uvicorn_server():
    """Starts the Uvicorn server in a subprocess bound to 0.0.0.0."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        APP_MODULE,
        "--host",
        "0.0.0.0",
        "--port",
        str(PORT),
        "--log-level",
        "warning",
    ]
    return subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), env=env)


def start_tunnel_process(service: str = "cloudflare"):
    """Launches high-performance Cloudflare Tunnel or OpenSSH reverse tunnel."""
    if service == "cloudflare":
        cf_bin = PROJECT_ROOT / "tools" / "cloudflared.exe"
        if not cf_bin.exists():
            raise FileNotFoundError("cloudflared.exe not found in tools/")
        cmd = [str(cf_bin), "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
    elif service == "localhost.run":
        cmd = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ServerAliveInterval=60",
            "-R",
            f"80:127.0.0.1:{PORT}",
            "nokey@localhost.run",
        ]
    elif service == "pinggy":
        cmd = [
            "ssh",
            "-p",
            "443",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ServerAliveInterval=60",
            "-R",
            f"0:127.0.0.1:{PORT}",
            "a.pinggy.io",
        ]
    else:
        raise ValueError(f"Unknown tunnel service: {service}")

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def extract_public_url(tunnel_proc, timeout: int = 15):
    """Monitors tunnel process output to extract the generated public HTTPS URL."""
    start_time = time.time()
    url = None

    while time.time() - start_time < timeout:
        line = tunnel_proc.stdout.readline()
        if not line:
            if tunnel_proc.poll() is not None:
                break
            time.sleep(0.1)
            continue

        # Pattern for Cloudflare (*.trycloudflare.com)
        match_cf = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match_cf:
            url = match_cf.group(0)
            break

        # Pattern for localhost.run (*.lhr.life)
        match_lhr = re.search(r"https://[a-zA-Z0-9.-]+\.lhr\.life", line)
        if match_lhr:
            url = match_lhr.group(0)
            break

        # Pattern for pinggy (*.pinggy.link or *.pinggy.io)
        match_pinggy = re.search(r"https://[a-zA-Z0-9.-]+\.pinggy\.(link|io)", line)
        if match_pinggy:
            url = match_pinggy.group(0)
            break

    return url



def print_banner(public_url: str, local_ip: str):
    """Renders a clear terminal dashboard for the host."""
    login_pub = f"{public_url}/landing" if public_url else "Generating..."
    login_lan = f"http://{local_ip}:{PORT}/landing"
    login_loc = f"http://localhost:{PORT}/landing"

    print("\n" + "=" * 80)
    print("           SME FINANCE COPILOT — LIVE PUBLIC SHARING ONLINE")
    print("=" * 80)
    print("  Status: ONLINE! Anyone worldwide can access as long as your PC is running.")
    print("=" * 80)
    print()
    print("  [1] 🌐 PUBLIC INTERNET LINK (Share this with remote users / evaluators):")
    print(f"      👉 {login_pub}")
    print("      (Copied to your clipboard! Just paste and send via WhatsApp / Email)")
    print()
    print("  [2] 📱 LOCAL WI-FI / LAN LINK (For phones and laptops on the SAME Wi-Fi):")
    print(f"      👉 {login_lan}")
    print()
    print("  [3] 💻 THIS PC (Localhost):")
    print(f"      👉 {login_loc}")
    print()
    print("  " + "-" * 76)
    print("  🔑 PRE-SEEDED DEMO PERSONAS FOR GUEST USERS:")
    print("     • Store Owner   : demo_owner       / demo12345 (or 1-Click Login button)")
    print("     • Accountant    : demo_accountant  / password123")
    print("     • Cashier       : demo_cashier     / password123")
    print("     • Bank Auditor  : demo_auditor     / password123")
    print("  " + "-" * 76)
    print("  ⚡ SPEED TIP:")
    print("     • Nearby / Same Wi-Fi (Mobile/Laptop): Use [2]! Instant 0-lag (0.01s).")
    print("     • Remote Users / Evaluators: Use [1] (HTTP GZip & Static Caching enabled).")
    print("  " + "-" * 76)
    print()
    print("  ⚠️  KEEP THIS WINDOW OPEN to keep the server and link active.")
    print("  🛑 Press CTRL+C at any time to stop sharing and shut down.")
    print("=" * 80 + "\n")


def main():
    local_ip = get_local_ip()
    print(f"[INFO] Initializing SME Finance Copilot on local network ({local_ip}:{PORT})...")

    # 1. Start Uvicorn background server
    uvicorn_proc = start_uvicorn_server()
    time.sleep(2)

    # 2. Establish public HTTPS tunnel (Cloudflare first for rock-solid stability and zero drops)
    cf_bin = PROJECT_ROOT / "tools" / "cloudflared.exe"
    if cf_bin.exists():
        print("[INFO] Creating rock-solid Cloudflare Tunnel (trycloudflare.com)...")
        tunnel_proc = start_tunnel_process("cloudflare")
        public_url = extract_public_url(tunnel_proc, timeout=12)
    else:
        tunnel_proc = None
        public_url = None

    # Fallback to localhost.run if Cloudflare binary is absent or failed
    if not public_url:
        print("[INFO] Creating secure public HTTPS tunnel (localhost.run)...")
        if tunnel_proc:
            try:
                tunnel_proc.terminate()
            except Exception:
                pass
        tunnel_proc = start_tunnel_process("localhost.run")
        public_url = extract_public_url(tunnel_proc, timeout=12)

    # Fallback to pinggy if localhost.run is busy
    if not public_url:
        print("[INFO] Trying backup tunnel provider (Pinggy)...")
        tunnel_proc.terminate()
        tunnel_proc = start_tunnel_process("pinggy")
        public_url = extract_public_url(tunnel_proc, timeout=12)

    if public_url and not public_url.startswith("https://tunnel.temporary"):
        copy_to_clipboard(f"{public_url}/landing")
        # Save to easy text file for host convenience
        try:
            link_file = PROJECT_ROOT / "LIVE_ONLINE_LINK.txt"
            link_file.write_text(
                f"SME FINANCE COPILOT — LIVE ONLINE LINK\n"
                f"=======================================\n"
                f"Public Internet Link:\n{public_url}/landing\n\n"
                f"Local Wi-Fi Link:\nhttp://{local_ip}:{PORT}/landing\n\n"
                f"Local PC Link:\nhttp://localhost:{PORT}/landing\n\n"
                f"Demo Personas:\n"
                f"Owner: demo_owner / demo12345\n"
                f"Accountant: demo_accountant / password123\n"
                f"Cashier: demo_cashier / password123\n"
                f"Auditor: demo_auditor / password123\n",
                encoding="utf-8"
            )
        except Exception:
            pass
    else:
        public_url = "https://tunnel.temporary.unavailable (Use Local Wi-Fi link)"

    # 3. Print the active dashboard
    print_banner(public_url, local_ip)

    # 4. Launch browser directly to the public link
    try:
        import webbrowser
        if public_url and not public_url.startswith("https://tunnel.temporary"):
            webbrowser.open(f"{public_url}/landing")
        else:
            webbrowser.open(f"http://localhost:{PORT}/landing")
    except Exception:
        pass

    # 5. Monitor and keep alive until CTRL+C
    def cleanup_and_exit(signum=None, frame=None):
        print("\n[INFO] Shutting down public tunnel and local server...")
        for p in [tunnel_proc, uvicorn_proc]:
            try:
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("[INFO] All services stopped safely. Thank you!")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    # Pipe tunnel logs gently in background
    def pipe_tunnel_logs():
        try:
            while True:
                line = tunnel_proc.stdout.readline()
                if not line:
                    break
                # Only print interesting connection notices or errors
                if "connection from" in line.lower() or "error" in line.lower():
                    print(f"  [Live Traffic] {line.strip()}")
        except Exception:
            pass

    log_thread = threading.Thread(target=pipe_tunnel_logs, daemon=True)
    log_thread.start()

    try:
        while True:
            time.sleep(1)
            # Check if server died
            if uvicorn_proc.poll() is not None:
                print("\n[ERROR] Local Uvicorn server exited unexpectedly.")
                break
            # Check if tunnel died
            if tunnel_proc.poll() is not None:
                print("\n[WARNING] Tunnel disconnected. Reconnecting in 3 seconds...")
                time.sleep(3)
                cf_bin = PROJECT_ROOT / "tools" / "cloudflared.exe"
                svc = "cloudflare" if cf_bin.exists() else "localhost.run"
                tunnel_proc = start_tunnel_process(svc)
                new_url = extract_public_url(tunnel_proc, timeout=12)
                if new_url:
                    public_url = new_url
                    copy_to_clipboard(f"{public_url}/landing")
                    print_banner(public_url, local_ip)
    except KeyboardInterrupt:
        cleanup_and_exit()


if __name__ == "__main__":
    main()
