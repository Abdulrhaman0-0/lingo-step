"""Diagnose real microphone/Vosk input without saving audio or student attempts."""
import argparse
import json
import os
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from letterstars.adapters.vosk_speech import VoskSpeechClassifier


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default=os.getenv("LINGOSTEP_MIC_DEVICE"),
                        help="Input device name or numeric index")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--duration", type=float, default=3)
    parser.add_argument("--wav", type=Path, help="Test an existing mono PCM16 WAV instead of the microphone")
    args = parser.parse_args()
    if args.attempts < 1 or not 1 <= args.duration <= 15:
        parser.error("Use attempts >= 1 and duration between 1 and 15 seconds")
    import sounddevice as sd
    import vosk
    if args.list_devices:
        print(sd.query_devices())
        print("Default input/output:", sd.default.device)
        return 0
    vosk.SetLogLevel(-1)
    rate, pcm = 16000, None
    if args.wav:
        with wave.open(str(args.wav), "rb") as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2 or source.getcomptype() != "NONE":
                parser.error("WAV must be uncompressed mono PCM16")
            rate = source.getframerate()
            pcm = source.readframes(source.getnframes())
    model_path = os.getenv("LINGOSTEP_VOSK_MODEL", str(ROOT / "models/speech/vosk-model-small-en-us-0.15"))
    speech = VoskSpeechClassifier(model_path, duration=args.duration, rate=rate, device=args.device)
    if not speech.ready:
        print("MODEL ERROR:", speech.error)
        return 1
    print("Model loaded. No audio files or student records will be saved.", flush=True)
    recognized = 0
    for i in range(1 if pcm is not None else args.attempts):
        if pcm is None:
            print(f"Attempt {i+1}: SPEAK NOW for {args.duration:g} seconds. Say one English letter name (e.g. bee).", flush=True)
        prediction = speech.recognize_letter(pcm)
        result = {
            "device": speech.last_device_name or "WAV file",
            "sample_rate": speech.last_sample_rate,
            "rms": round(speech.last_audio_rms, 1),
            "peak": speech.last_audio_peak,
            "transcript": speech.last_transcript,
            "letter": prediction.label if prediction else None,
            "confidence": round(prediction.confidence, 3) if prediction else None,
            "accepted": prediction is not None and prediction.confidence >= .65,
            "issue": speech.last_issue,
        }
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if result["accepted"]:
            recognized += 1
        elif speech.last_issue == "quiet":
            print("INPUT TOO QUIET: check selected microphone, mute and capture volume.", flush=True)
    print(f"Accepted {recognized} of {1 if pcm is not None else args.attempts} attempts at confidence >= 0.65.")
    return 0 if recognized else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"DIAGNOSTIC ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
