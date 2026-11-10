#!/usr/bin/env python3
"""Install reviewed LingoStep A-Z+others model ZIP; no network access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

EXPECTED_SHA256 = "61c70d1063d369dc2fc1625f941204938edd26b0aacccb237d8b8a92a4fea394"
LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["others"]

def install(path, target):
    with zipfile.ZipFile(path) as z:
        names = {Path(name).name: name for name in z.namelist() if not name.endswith("/")}
        if not {"model_unquant.tflite", "labels.txt"}.issubset(names):
            raise ValueError("Missing model_unquant.tflite or labels.txt")
        if z.getinfo(names["model_unquant.tflite"]).file_size > 100_000_000:
            raise ValueError("Invalid model size")
        binary = z.read(names["model_unquant.tflite"])
        labels_text = z.read(names["labels.txt"]).decode("utf-8-sig")
    sha = hashlib.sha256(binary).hexdigest()
    if sha != EXPECTED_SHA256 or binary[4:8] != b"TFL3":
        raise ValueError("Wrong or invalid model. No changes applied.")
    rows = [line.strip().split(maxsplit=1) for line in labels_text.splitlines() if line.strip()]
    if rows != [[str(i), label] for i, label in enumerate(LABELS)]:
        raise ValueError("Labels mismatch: expected indexed A-Z + others. No changes applied.")
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target, prefix=".model-", suffix=".tflite", delete=False) as tmp:
        tmp.write(binary)
        tmp.flush()
        os.fsync(tmp.fileno())
        staged = Path(tmp.name)
    os.replace(staged, target / "model.tflite")
    (target / "labels.txt").write_text(labels_text, encoding="utf-8")
    config = {
        "labels": LABELS,
        "channel_order": "RGB",
        "input_mean": 127.5,
        "input_std": 127.5,
        "notes": "SHA256 matches uploaded LingoStep A-Z+others model. Validate input preprocessing/real accuracy on target."
    }
    (target / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("Installed 27-class model (A-Z + others) at", target)
    print("SHA256:", sha)
    print("Accuracy and camera compatibility still require real tests.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_file", type=Path)
    parser.add_argument("--target", type=Path,
                        default=Path(__file__).resolve().parents[1] / "models" / "image")
    args = parser.parse_args()
    install(args.zip_file, args.target)
