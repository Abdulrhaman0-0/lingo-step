"""Small persistent-config loader for the PythonAnywhere school prototype."""
import json
from pathlib import Path
import secrets
import os


def prepare_settings(directory, public_url):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/"hosting-settings.json"
    if path.exists():
        settings = json.loads(path.read_text(encoding="utf-8"))
    else:
        settings = {"session_secret": secrets.token_urlsafe(48),
                    "device_token": secrets.token_urlsafe(32)}
    if (not isinstance(settings, dict) or
            len(settings.get("session_secret", "")) < 32 or
            len(settings.get("device_token", "")) < 24):
        raise ValueError("Invalid hosting settings; restore the existing file, do not regenerate keys")
    settings["public_url"] = public_url.rstrip("/")
    # Keys stay stable across setup/reloads, preserving guardian logins and pairing.
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump(settings, out, indent=2)
    return settings


def create_hosted_app(directory=None):
    from cloud.portal import create_app
    directory = Path(directory) if directory else Path(__file__).resolve().parent/"data"
    path = directory/"hosting-settings.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    return create_app({"SECRET_KEY": settings["session_secret"],
                       "DEVICE_TOKEN": settings["device_token"],
                       "DB_PATH": str(directory/"portal.db"),
                       "SESSION_COOKIE_SECURE": True})
