"""Benchmarks for the actual LingoStep TFLite camera and Vosk speech adapters.

Usage:
    python scripts/benchmark_ai.py camera --letters ABCDE --repeats 10 --others 10
    python scripts/benchmark_ai.py mic --letters ABCDE --repeats 10
    python scripts/benchmark_ai.py image-files --manifest data/image-test.csv
    python scripts/benchmark_ai.py speech-files --manifest data/speech-test.csv
    python scripts/benchmark_ai.py report results/benchmarks/camera_....csv

No microphone recordings or camera photos are saved by live test commands.
Accuracy is always computed against independent, operator-labelled ground truth.
"""
import argparse
import csv
from collections import Counter, deque
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from letterstars.config import CONFIDENCE_THRESHOLD, STABLE_FRAMES, CAMERA_INDEX
from letterstars.adapters.image_model import TFLiteImageClassifier
from letterstars.adapters.vosk_speech import VoskSpeechClassifier

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
OTHER = "OTHER"
UNKNOWN = "UNKNOWN"
FIELDS = (
    "timestamp_utc", "model", "device", "trial", "expected", "predicted",
    "raw_predicted", "confidence", "raw_confidence", "correct", "raw_correct",
    "status", "frames", "capture_ms", "inference_ms", "response_ms",
    "elapsed_ms", "notes",
)


def canonical(value):
    value = (value or "").strip().upper()
    if value in ("OTHERS", "OTHER", "NO_CARD", "NOISE"):
        return OTHER
    if value in ("", "NONE", "UNKNOWN", "REJECTED"):
        return UNKNOWN
    if len(value) == 1 and value in LETTERS:
        return value
    raise ValueError("Invalid letter label: " + repr(value))


def is_correct(expected, prediction):
    """A true negative OTHER is successful when it is rejected as unknown."""
    expected, prediction = canonical(expected), canonical(prediction)
    if expected == OTHER:
        return prediction in (OTHER, UNKNOWN)
    return expected == prediction


def parse_letters(value):
    result = "".join(value.upper().replace(",", "").split())
    if not result or len(result) != len(set(result)) or any(c not in LETTERS for c in result):
        raise ValueError("--letters must be unique letters A-Z (example: ABCDE or A,B,C,D,E)")
    return list(result)


def percentile(numbers, pct):
    data = sorted(float(n) for n in numbers)
    if not data:
        return None
    index = (len(data) - 1) * pct / 100.0
    lower = int(index)
    upper = min(lower + 1, len(data) - 1)
    return round(data[lower] + (data[upper] - data[lower]) * (index - lower), 2)


def numeric(rows, key):
    return [float(r[key]) for r in rows if r.get(key) not in (None, "")]


def summarize(rows):
    """Return measured, descriptive statistics; never invent a pass rate."""
    rows = list(rows)
    if not rows:
        raise ValueError("No benchmark rows to summarize")
    models = {r["model"] for r in rows}
    if len(models) != 1:
        raise ValueError("One report must contain a single benchmark mode")
    valid = [r for r in rows if canonical(r["expected"]) != OTHER]
    negatives = [r for r in rows if canonical(r["expected"]) == OTHER]
    def accuracy(items, field="correct"):
        return round(100.0 * sum(int(r[field]) for r in items) / len(items), 2) if items else None
    def timings(key, data):
        values = numeric(data, key)
        return {
            "n": len(values),
            "mean_ms": round(statistics.mean(values), 2) if values else None,
            "median_ms": percentile(values, 50),
            "p95_ms": percentile(values, 95),
            "max_ms": round(max(values), 2) if values else None,
        }
    ordered = sorted(set(r["expected"] for r in valid))
    per_class = {
        letter: {
            "trials": sum(r["expected"] == letter for r in valid),
            "correct": sum(r["expected"] == letter and int(r["correct"]) for r in valid),
            "accuracy_pct": accuracy([r for r in valid if r["expected"] == letter]),
        }
        for letter in ordered
    }
    return {
        "model": rows[0]["model"],
        "device": rows[0].get("device"),
        "total_trials": len(rows),
        "letter_trials": len(valid),
        "letter_correct": sum(int(r["correct"]) for r in valid),
        "letter_accuracy_pct": accuracy(valid),
        "raw_letter_accuracy_pct": accuracy(valid, "raw_correct"),
        "negative_trials": len(negatives),
        "negative_rejection_pct": accuracy(negatives),
        "all_trials_accuracy_pct": accuracy(rows),
        "unknown_or_rejected_on_letters": sum(
            r["predicted"] in (UNKNOWN, OTHER) for r in valid
        ),
        "errors": sum(r.get("status") == "error" for r in rows),
        "inference_ms": timings("inference_ms", rows),
        "response_ms": timings("response_ms", rows),
        "capture_ms": timings("capture_ms", rows),
        "elapsed_ms": timings("elapsed_ms", rows),
        "per_letter": per_class,
    }


def write_report(csv_path):
    csv_path = Path(csv_path)
    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    summary = summarize(rows)
    output = csv_path.with_name(csv_path.stem + "_summary.json")
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    def pct(n):
        return "N/A" if n is None else f"{n:.2f}%"
    def ms(part):
        return "N/A" if part["mean_ms"] is None else (
            f'{part["mean_ms"]:.2f} / {part["median_ms"]:.2f} / {part["p95_ms"]:.2f}'
        )
    lines = [
        "# LingoStep benchmark: " + summary["model"],
        "",
        f'- Device: {summary["device"]}',
        f'- Trials: {summary["total_trials"]} ({summary["letter_trials"]} letters, '
        f'{summary["negative_trials"]} negative/OTHER)',
        f'- **Letter accuracy: {pct(summary["letter_accuracy_pct"])}** '
        f'({summary["letter_correct"]}/{summary["letter_trials"]})',
        f'- Raw first-prediction accuracy (letters): {pct(summary["raw_letter_accuracy_pct"])}',
        f'- Negative/OTHER rejection: {pct(summary["negative_rejection_pct"])}',
        f'- All trials accuracy: {pct(summary["all_trials_accuracy_pct"])}',
        f'- Unknown/rejected letter attempts: {summary["unknown_or_rejected_on_letters"]}',
        f'- Failed trials due to errors: {summary["errors"]}',
        "",
        "## Response-time statistics (milliseconds)",
        "",
        "| Metric | Mean / Median / P95 | Samples |",
        "|---|---|---:|",
        f'| Inference | {ms(summary["inference_ms"])} | {summary["inference_ms"]["n"]} |',
        f'| Response | {ms(summary["response_ms"])} | {summary["response_ms"]["n"]} |',
        f'| Capture / recording | {ms(summary["capture_ms"])} | {summary["capture_ms"]["n"]} |',
        f'| Total elapsed | {ms(summary["elapsed_ms"])} | {summary["elapsed_ms"]["n"]} |',
        "",
        "## Per-letter results",
        "",
        "| Letter | Correct | Total | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for letter, item in summary["per_letter"].items():
        lines.append(f'| {letter} | {item["correct"]} | {item["trials"]} | '
                     f'{pct(item["accuracy_pct"])} |')
    lines += [
        "",
        "Accuracy counts failed/unknown letter outputs as incorrect. For true "
        "OTHER/no-card cases, explicit OTHER or UNKNOWN is a correct rejection. "
        "No figure here proves generalization to unseen people/lighting unless "
        "the trial data was collected independently of training/tuning.",
        "",
        "Camera live inference is average per frame; live response is time "
        "from trial trigger to stable 5-frame letter decision at the app "
        "confidence threshold (not exact GUI rendering/cloud/audio latency). "
        "A timeout/rejection has no positive-decision response timestamp.",
        "",
        "Mic live response includes the configured fixed recording window "
        "(default 3 seconds) and the Vosk processing. Inference excludes capture. "
        "Offline files have no real sensor/GUI response latency.",
        "",
        "Vosk recognition accuracy measures whether the spoken LETTER NAME "
        "was identified; it does not grade pronunciation quality.",
        "",
    ]
    markdown = csv_path.with_name(csv_path.stem + "_summary.md")
    markdown.write_text("\n".join(lines), encoding="utf-8")
    # Include unknown and reject columns; this is a count matrix, not probabilities.
    columns = list(LETTERS) + [OTHER, UNKNOWN]
    confusion = csv_path.with_name(csv_path.stem + "_confusion.csv")
    with confusion.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["expected"] + columns)
        for actual in sorted(set(canonical(r["expected"]) for r in rows)):
            counts = Counter(canonical(r["predicted"]) for r in rows if canonical(r["expected"]) == actual)
            writer.writerow([actual] + [counts[c] for c in columns])
    print(f"\nLetter accuracy: {pct(summary['letter_accuracy_pct'])} "
          f"({summary['letter_correct']}/{summary['letter_trials']})")
    print("Negative/OTHER rejection:", pct(summary["negative_rejection_pct"]))
    print("Mean model inference:", summary["inference_ms"]["mean_ms"], "ms")
    print("Mean live response:", summary["response_ms"]["mean_ms"], "ms")
    print("Saved:", output, markdown, confusion, sep="\n  ")
    return summary


def prepare_output(mode, requested):
    if requested:
        destination = Path(requested)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        destination = ROOT / "results" / "benchmarks" / f"{mode}_{stamp}.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Explicitly do not overwrite evidence from an earlier test.
    with destination.open("x", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writeheader()
    return destination


def append_row(path, data):
    record = {field: data.get(field, "") for field in FIELDS}
    record["timestamp_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record["device"] = platform.node()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(record)


def trial_order(letters, repeats, others, seed):
    trials = letters * repeats + [OTHER] * others
    random.Random(seed).shuffle(trials)
    return trials


def run_camera(args):
    from letterstars.adapters.camera import OpenCVCamera
    model = TFLiteImageClassifier(ROOT / "models" / "image")
    if not model.ready:
        raise RuntimeError("TFLite model unavailable: " + model.error)
    letters = parse_letters(args.letters)
    if any(not model.supports_letter(letter) for letter in letters):
        raise ValueError("Requested letter not in installed TFLite model")
    path = prepare_output("camera", args.output)
    camera = OpenCVCamera(args.camera_index)
    trials = trial_order(letters, args.repeats, args.others, args.seed)
    print(f"Camera: {len(trials)} manual trials. Show a new real card for each trial.")
    print("OTHER = no card or irrelevant object. Do NOT use training images.")
    print(f"Threshold {CONFIDENCE_THRESHOLD:.2f}, stable frames {STABLE_FRAMES}, "
          "GUI frame pause approx 170 ms; no photos are saved.")
    camera.open()
    try:
        for _ in range(5):
            camera.read()  # warm-up, excluded
        for index, expected in enumerate(trials, 1):
            answer = input(f"\n[{index}/{len(trials)}] Show {expected} to camera; "
                           "press ENTER to capture (q=finish): ")
            if answer.strip().lower() == "q":
                break
            start = time.perf_counter()
            window = deque(maxlen=STABLE_FRAMES)
            raw = UNKNOWN
            raw_conf = ""
            pred_label = UNKNOWN
            conf = ""
            status = "timeout"
            frames = 0
            capture_samples = []
            infer_samples = []
            try:
                while (time.perf_counter() - start) < args.timeout:
                    t0 = time.perf_counter()
                    frame = camera.read()
                    capture_samples.append((time.perf_counter() - t0) * 1000)
                    if frame is None:
                        raise RuntimeError("Camera frame read failed")
                    t1 = time.perf_counter()
                    prediction = model.predict(frame)
                    infer_samples.append((time.perf_counter() - t1) * 1000)
                    frames += 1
                    label = prediction.label if prediction else OTHER
                    score = prediction.confidence if prediction else None
                    if frames == 1:
                        raw, raw_conf = label, round(score, 4) if score is not None else ""
                    valid = label if score is not None and score >= CONFIDENCE_THRESHOLD else None
                    window.append((valid, label, score))
                    if len(window) >= STABLE_FRAMES:
                        candidates = [v[0] for v in window]
                        if len(set(candidates)) == 1 and candidates[0] is not None:
                            pred_label = candidates[0]
                            conf = round(window[-1][2], 4)
                            status = "recognized"
                            break
                        if all(v[1] == OTHER for v in window):
                            pred_label = OTHER
                            status = "other_class"
                            break
                    time.sleep(args.frame_pause)
            except Exception as exc:
                status = "error"
                error_note = str(exc)
            else:
                error_note = ""
            elapsed = round((time.perf_counter() - start)*1000, 2)
            append_row(path, {
                "model": "camera_live", "trial": index,
                "expected": expected, "predicted": pred_label,
                "raw_predicted": raw, "confidence": conf, "raw_confidence": raw_conf,
                "correct": int(is_correct(expected, pred_label) and status != "error"),
                "raw_correct": int(is_correct(expected, raw) and status != "error"),
                "status": status, "frames": frames,
                "capture_ms": round(statistics.mean(capture_samples), 2) if capture_samples else "",
                "inference_ms": round(statistics.mean(infer_samples), 2) if infer_samples else "",
                "response_ms": elapsed if status in ("recognized", "other_class") else "",
                "elapsed_ms": elapsed, "notes": error_note,
            })
            print(f"  expected={expected} predicted={pred_label} "
                  f"status={status} inference="
                  f"{round(statistics.mean(infer_samples), 2) if infer_samples else 'N/A'} ms "
                  f"trial_elapsed={elapsed} ms")
    except KeyboardInterrupt:
        print("\nInterrupted; collected trials were saved.")
    finally:
        camera.close()
    print("CSV:", path)
    with path.open(encoding="utf-8", newline="") as f:
        if any(csv.DictReader(f)):
            write_report(path)
    return 0


def run_mic(args):
    model_path = Path(os.getenv("LINGOSTEP_VOSK_MODEL",
                                 str(ROOT / "models" / "speech" / "vosk-model-small-en-us-0.15")))
    model = VoskSpeechClassifier(model_path, duration=args.duration, device=args.device)
    if not model.ready:
        raise RuntimeError("Vosk unavailable: " + model.error)
    letters = parse_letters(args.letters)
    trials = trial_order(letters, args.repeats, args.others, args.seed)
    path = prepare_output("mic", args.output)
    print(f"Mic: {len(trials)} trials; speak each displayed LETTER NAME.")
    print(f"Recording window: {args.duration:g}s. Threshold 0.65. "
          "No audio files are stored. OTHER = silence/unrelated speech.")
    try:
        for index, expected in enumerate(trials, 1):
            answer = input(f"\n[{index}/{len(trials)}] Ready to SAY {expected}? "
                           "Press ENTER (q=finish): ")
            if answer.strip().lower() == "q":
                break
            begin = time.perf_counter()
            try:
                prediction = model.recognize_letter()
                total_ms = round((time.perf_counter()-begin)*1000, 2)
                raw = prediction.label if prediction else UNKNOWN
                raw_conf = round(prediction.confidence, 4) if prediction else ""
                accepted = prediction is not None and prediction.confidence >= 0.65
                label = raw if accepted else UNKNOWN
                status = "recognized" if accepted else "rejected"
                notes = "Vosk text: " + model.last_transcript
                capture = round(model.last_capture_ms, 2)
                infer = round(model.last_decode_ms, 2)
                confidence = raw_conf if accepted else ""
            except Exception as exc:
                total_ms = round((time.perf_counter()-begin)*1000, 2)
                raw, label, raw_conf, confidence = UNKNOWN, UNKNOWN, "", ""
                capture, infer, status, notes = "", "", "error", str(exc)
            append_row(path, {
                "model": "mic_live", "trial": index, "expected": expected,
                "predicted": label, "raw_predicted": raw,
                "confidence": confidence, "raw_confidence": raw_conf,
                "correct": int(is_correct(expected, label) and status != "error"),
                "raw_correct": int(is_correct(expected, raw) and status != "error"),
                "status": status, "frames": "",
                "capture_ms": capture, "inference_ms": infer,
                "response_ms": total_ms, "elapsed_ms": total_ms, "notes": notes,
            })
            print(f"  expected={expected} heard={label} status={status} "
                  f"response={total_ms} ms; decoder={infer} ms")
    except KeyboardInterrupt:
        print("\nInterrupted; collected trials were saved.")
    print("CSV:", path)
    with path.open(encoding="utf-8", newline="") as f:
        if any(csv.DictReader(f)):
            write_report(path)
    return 0


def load_manifest(path):
    path = Path(path).resolve()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not {"path", "expected"} <= set(reader.fieldnames or ()):
            raise ValueError("Manifest needs columns: path,expected")
        rows = list(reader)
    if not rows:
        raise ValueError("Manifest has no samples")
    result = []
    for row in rows:
        actual = canonical(row["expected"])
        if actual == UNKNOWN:
            raise ValueError("Ground-truth label cannot be UNKNOWN")
        file = Path(row["path"])
        if not file.is_absolute():
            file = path.parent / file
        result.append((file, actual))
    return result


def run_image_files(args):
    import cv2
    model = TFLiteImageClassifier(ROOT / "models" / "image")
    if not model.ready:
        raise RuntimeError("TFLite model unavailable: " + model.error)
    manifest = load_manifest(args.manifest)
    output = prepare_output("image_files", args.output)
    for i, (file, expected) in enumerate(manifest, 1):
        t0 = time.perf_counter()
        frame = cv2.imread(str(file))
        if frame is None:
            raw, label, confidence, status, inf, note = UNKNOWN, UNKNOWN, "", "error", "", f"Cannot read {file}"
        else:
            try:
                tic = time.perf_counter()
                p = model.predict(frame)
                inf = round((time.perf_counter() - tic) * 1000, 2)
                raw = p.label if p else OTHER
                confidence = round(p.confidence, 4) if p else ""
                label = raw if (p is None or p.confidence >= CONFIDENCE_THRESHOLD) else UNKNOWN
                status = "recognized" if label in LETTERS else "rejected"
                note = file.name
            except Exception as exc:
                raw, label, confidence, status, inf, note = UNKNOWN, UNKNOWN, "", "error", "", str(exc)
        elapsed = round((time.perf_counter()-t0)*1000, 2)
        append_row(output, {
            "model": "image_files", "trial": i, "expected": expected,
            "predicted": label, "raw_predicted": raw,
            "confidence": confidence, "raw_confidence": confidence,
            "correct": int(is_correct(expected, label) and status != "error"),
            "raw_correct": int(is_correct(expected, raw) and status != "error"),
            "status": status, "inference_ms": inf,
            "elapsed_ms": elapsed, "notes": note,
        })
    write_report(output)
    return 0


def run_speech_files(args):
    manifest = load_manifest(args.manifest)
    model_path = Path(os.getenv("LINGOSTEP_VOSK_MODEL",
                      str(ROOT / "models" / "speech" / "vosk-model-small-en-us-0.15")))
    model = VoskSpeechClassifier(model_path)
    if not model.ready:
        raise RuntimeError("Vosk unavailable: " + model.error)
    output = prepare_output("speech_files", args.output)
    for i, (file, expected) in enumerate(manifest, 1):
        start = time.perf_counter()
        try:
            with wave.open(str(file), "rb") as wav:
                if (wav.getnchannels() != 1 or wav.getsampwidth() != 2
                        or wav.getframerate() != 16000 or wav.getcomptype() != "NONE"):
                    raise ValueError("Use 16kHz mono PCM16 uncompressed WAV: " + str(file))
                pcm = wav.readframes(wav.getnframes())
            prediction = model.recognize_letter(pcm)
            raw = prediction.label if prediction else UNKNOWN
            raw_conf = round(prediction.confidence, 4) if prediction else ""
            accepted = prediction is not None and prediction.confidence >= 0.65
            label = raw if accepted else UNKNOWN
            status = "recognized" if accepted else "rejected"
            infer = round(model.last_decode_ms, 2)
            notes = file.name + " / " + model.last_transcript
        except Exception as exc:
            raw, label, raw_conf, status, infer, notes = UNKNOWN, UNKNOWN, "", "error", "", str(exc)
        elapsed = round((time.perf_counter()-start)*1000, 2)
        append_row(output, {
            "model": "speech_files", "trial": i, "expected": expected,
            "predicted": label, "raw_predicted": raw,
            "confidence": raw_conf, "raw_confidence": raw_conf,
            "correct": int(is_correct(expected, label) and status != "error"),
            "raw_correct": int(is_correct(expected, raw) and status != "error"),
            "status": status, "inference_ms": infer,
            "elapsed_ms": elapsed, "notes": notes,
        })
    write_report(output)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("camera", "mic"):
        p = sub.add_parser(mode)
        p.add_argument("--letters", default=LETTERS, help="E.g. ABCDE or A,B,C")
        p.add_argument("--repeats", type=int, default=10, help="Independent trials per letter")
        p.add_argument("--others", type=int, default=0, help="Optional unrelated inputs")
        p.add_argument("--seed", type=int, default=27)
        p.add_argument("--output", type=Path, help="New CSV; never overwritten")
        if mode == "camera":
            p.add_argument("--camera-index", type=int, default=CAMERA_INDEX)
            p.add_argument("--timeout", type=float, default=5.0)
            p.add_argument("--frame-pause", type=float, default=0.170)
        else:
            p.add_argument("--duration", type=float, default=3.0)
            p.add_argument("--device", default=os.getenv("LINGOSTEP_MIC_DEVICE"))
    for mode in ("image-files", "speech-files"):
        p = sub.add_parser(mode)
        p.add_argument("--manifest", type=Path, required=True, help="CSV with path,expected")
        p.add_argument("--output", type=Path)
    p = sub.add_parser("report")
    p.add_argument("csv_file", type=Path)
    args = parser.parse_args(argv)
    if args.mode in ("camera", "mic"):
        if args.repeats < 1 or args.others < 0:
            parser.error("--repeats must be >=1; --others >=0")
        if args.mode == "camera" and (args.timeout <= 0 or args.frame_pause < 0):
            parser.error("Camera timeout must be >0; frame pause must be >=0")
        if args.mode == "mic" and not 1 <= args.duration <= 15:
            parser.error("Microphone duration must be between 1 and 15 seconds")
    try:
        if args.mode == "report":
            write_report(args.csv_file)
            return 0
        return {
            "camera": run_camera, "mic": run_mic,
            "image-files": run_image_files, "speech-files": run_speech_files,
        }[args.mode](args)
    except (RuntimeError, ValueError, OSError, ImportError) as exc:
        print(f"BENCHMARK ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
