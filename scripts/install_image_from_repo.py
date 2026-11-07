"""One-time model setup from a ZIP committed to GitHub.

Place the original Embedded Image.zip in models/image/ through GitHub's
web UI, then run this script on Raspberry Pi after git pull.
No manual model transfer to Pi is needed.
"""
from pathlib import Path
import json
import zipfile

root = Path(__file__).resolve().parents[1] / "models" / "image"
zipped = root / "Embedded Image.zip"
needed = ("model.json", "metadata.json", "weights.bin")
if all((root / x).is_file() for x in needed):
    print("Image AI installed.")
elif not zipped.is_file():
    raise SystemExit("Missing models/image/Embedded Image.zip. Upload it to GitHub repo first.")
else:
    with zipfile.ZipFile(zipped) as z:
        for name in needed:
            candidates = [entry for entry in z.namelist() if Path(entry).name == name and not entry.endswith("/")]
            if len(candidates) != 1:
                raise SystemExit(f"Expected exactly one {name} in archive")
            (root / name).write_bytes(z.read(candidates[0]))
    meta = json.loads((root / "metadata.json").read_text())
    assert meta["labels"] == list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), "Expected A–Z labels"
    print("Image model extracted and labels validated.")
