"""Prepare persistent web keys and a private Pi connection file on the host."""
import argparse
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Public HTTPS site URL")
    args = parser.parse_args()
    url = args.url.rstrip("/")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path:
        parser.error("Use only the site's HTTPS origin, e.g. https://yourname.pythonanywhere.com")
    from cloud.hosting import prepare_settings, create_hosted_app
    directory = ROOT/"cloud/data"
    settings = prepare_settings(directory, url)
    app = create_hosted_app(directory)
    assert app.test_client().get("/api/v1/health").json == {"status": "ok"}
    private_export = directory/"pi-cloud-settings.json"
    fd = os.open(str(private_export), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump({"url": url, "token": settings["device_token"]}, out, indent=2)
    print("Host configuration and database ready. Keys were not printed.")
    print("Private Raspberry connection file:", private_export)
    print("Source directory:", ROOT)
    print("WSGI configuration:\n")
    print("import sys")
    print(f"sys.path.insert(0, {str(ROOT)!r})")
    print("from cloud.pythonanywhere_wsgi import application")


if __name__ == "__main__":
    main()
