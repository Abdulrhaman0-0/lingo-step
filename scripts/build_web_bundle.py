"""Build a small allowlisted source ZIP for PythonAnywhere; never include keys/data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def build_bundle(destination):
    files = ["cloud/portal.py", "cloud/hosting.py", "cloud/pythonanywhere_wsgi.py",
             "cloud/requirements-hosting.txt", "letterstars/domain/pairing.py",
             "scripts/setup_hosted_web.py", "scripts/install_pythonanywhere.py"]
    for optional in ("cloud/__init__.py", "letterstars/__init__.py", "letterstars/domain/__init__.py"):
        if (ROOT/optional).is_file():
            files.append(optional)
    for directory in ("cloud/templates", "cloud/static"):
        files.extend(str(p.relative_to(ROOT)).replace("\\", "/")
                     for p in (ROOT/directory).rglob("*") if p.is_file())
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for relative in files:
            archive.write(ROOT/relative, "lingostep-web/"+relative)
    return destination


if __name__ == "__main__":
    output = build_bundle(ROOT/".venv/lingostep-web.zip")
    print(output)
    print("Source only; no child data, tokens, models or virtual environment included.")
