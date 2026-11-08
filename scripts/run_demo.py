"""Run the school prototype locally: child app + parent website in one command."""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def demo_settings(path):
    """Keep local keys stable so guardian sessions and child pairing survive restart."""
    if path.exists():
        settings = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(settings, dict) or
                not isinstance(settings.get("session_secret"), str) or
                len(settings["session_secret"]) < 32 or
                not isinstance(settings.get("device_token"), str) or
                len(settings["device_token"]) < 24):
            raise ValueError("Invalid local demo settings; restore data/demo-settings.json from your local backup.")
        return settings
    settings = {"session_secret": secrets.token_urlsafe(48),
                "device_token": secrets.token_urlsafe(32)}
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create prevents overwriting keys used by an existing demo.
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(settings, output, indent=2)
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-only", action="store_true", help="Run only the local website")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    try:
        from werkzeug.serving import make_server
        from cloud.portal import create_app
    except ImportError as exc:
        raise SystemExit("Install demo dependencies first: python -m pip install -r requirements-demo.txt") from exc
    os.chdir(ROOT)
    settings = demo_settings(ROOT/"data/demo-settings.json")
    url = f"http://127.0.0.1:{args.port}"
    # Local demo is isolated from any externally configured production server.
    os.environ["LINGOSTEP_CLOUD_URL"] = url
    os.environ["LINGOSTEP_DEVICE_TOKEN"] = settings["device_token"]
    app = create_app({"SECRET_KEY": settings["session_secret"],
                      "DEVICE_TOKEN": settings["device_token"],
                      "DB_PATH": str(ROOT/"data/demo-portal.db"),
                      "SESSION_COOKIE_SECURE": False})
    server = make_server("127.0.0.1", args.port, app, threaded=True)
    print(f"Parent website: {url}", flush=True)
    print("Local school demo only. Open the link on this device or through an SSH tunnel.", flush=True)
    if args.web_only:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        from main import build_app
        build_app().run()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
