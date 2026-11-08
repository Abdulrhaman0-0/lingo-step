"""Load saved Pi hosting settings without overriding explicit session settings."""
import json
import os
from pathlib import Path


def load_cloud_settings(path):
    path = Path(path)
    if not path.exists():
        return
    settings = json.loads(path.read_text(encoding="utf-8"))
    url, token = settings.get("url", ""), settings.get("token", "")
    if not isinstance(url, str) or not isinstance(token, str) or len(token) < 24:
        raise ValueError("Invalid cloud connection file; rerun scripts/configure_cloud.py")
    # The local demo sets both environment variables and remains independent.
    if not os.getenv("LINGOSTEP_CLOUD_URL") and not os.getenv("LINGOSTEP_DEVICE_TOKEN"):
        os.environ["LINGOSTEP_CLOUD_URL"] = url
        os.environ["LINGOSTEP_DEVICE_TOKEN"] = token
