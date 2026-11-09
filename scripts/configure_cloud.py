"""Configure the Pi's hosted connection and queue prior progress once."""
import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def save_connection(source, target, progress_path):
    settings = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(settings, dict):
        raise ValueError("Expected a JSON connection file")
    return save_settings(settings, target, progress_path)


def save_settings(settings, target, progress_path):
    url, token = settings.get("url"), settings.get("token")
    parsed = urlsplit(url) if isinstance(url, str) else None
    if (not parsed or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or
            parsed.path not in ("", "/") or parsed.query or parsed.fragment or
            not isinstance(token, str) or len(token) < 24):
        raise ValueError("Connection file must contain an HTTPS site URL and valid token")
    settings = {"url": url.rstrip("/"), "token": token}
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
    if previous != settings and Path(progress_path).exists():
        from letterstars.infrastructure.student_progress import StudentProgressStore
        store = StudentProgressStore(progress_path)
        with store._connect() as db:
            db.execute("UPDATE attempts SET synced_at=NULL")
    fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=".cloud-settings-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(settings, out, indent=2)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return settings["url"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("connection_file", nargs="?", type=Path, help="Private pi-cloud-settings.json")
    source.add_argument("--url", help="Hosted HTTPS URL. Enter the device token at the hidden prompt.")
    args = parser.parse_args()
    from letterstars.config import APP_DATA
    target = ROOT/"data/cloud-settings.json"
    progress = APP_DATA/"progress.db"
    try:
        if args.url:
            token = getpass("Device token (hidden): ").strip()
            url = save_settings({"url": args.url, "token": token}, target, progress)
        else:
            url = save_connection(args.connection_file, target, progress)
    except ValueError as exc:
        parser.error(str(exc))
    print("Cloud connection saved:", url)
    print("Existing progress queued for upload if this is a new connection. No student data was deleted.")
    print("Next: bash scripts/run_pi.sh (not run_demo.py)")


if __name__ == "__main__":
    main()
