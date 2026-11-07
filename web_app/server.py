"""LetterStars: local browser frontend + offline Vosk API for Raspberry Pi 5.
Run from repository root: python3 -m web_app.server
The UI's Teachable Machine TensorFlow.js model executes in Chromium.
"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote
import io
import json
import os
import re
import wave

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web_app"
IMAGE = ROOT / "models" / "image"
SPEECH = Path(os.getenv("LETTERSTARS_VOSK_MODEL", str(ROOT / "models" / "speech" / "vosk-model-small-en-us-0.15")))
HOST = os.getenv("LETTERSTARS_HOST", "127.0.0.1")
PORT = int(os.getenv("LETTERSTARS_PORT", "8765"))
VALID_LETTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ALIASES = {
    "ay": "A", "a": "A", "bee": "B", "be": "B", "b": "B",
    "see": "C", "sea": "C", "c": "C", "dee": "D", "d": "D",
    "ee": "E", "e": "E", "eff": "F", "f": "F", "gee": "G", "g": "G",
    "aitch": "H", "h": "H", "eye": "I", "i": "I", "jay": "J", "j": "J",
    "kay": "K", "k": "K", "ell": "L", "l": "L", "em": "M", "m": "M",
    "en": "N", "n": "N", "oh": "O", "o": "O", "pee": "P", "p": "P",
    "cue": "Q", "queue": "Q", "q": "Q", "are": "R", "r": "R",
    "ess": "S", "s": "S", "tee": "T", "t": "T", "you": "U", "u": "U",
    "vee": "V", "v": "V", "double you": "W", "w": "W", "ex": "X", "x": "X",
    "why": "Y", "y": "Y", "zee": "Z", "zed": "Z", "z": "Z",
}
# Do not force a single-letter grammar: phonetic letter names are easily confused.
_VOSK_MODEL = None


def get_model():
    global _VOSK_MODEL
    if _VOSK_MODEL is None:
        if not SPEECH.is_dir():
            raise RuntimeError("Vosk model absent: " + str(SPEECH))
        from vosk import Model
        _VOSK_MODEL = Model(str(SPEECH))
    return _VOSK_MODEL


def analyze_audio(data):
    from vosk import KaldiRecognizer
    if len(data) > 2_000_000:
        raise ValueError("Recording exceeds 2 MB")
    with wave.open(io.BytesIO(data), "rb") as sound:
        if sound.getnchannels() != 1 or sound.getsampwidth() != 2 or sound.getframerate() != 16000:
            raise ValueError("Expected mono 16-bit PCM WAV at 16000 Hz")
        pcm = sound.readframes(sound.getnframes())
    if len(pcm) < 3200:
        raise ValueError("Recording too short")
    recognizer = KaldiRecognizer(get_model(), 16000)
    recognizer.SetWords(True)
    recognizer.AcceptWaveform(pcm)
    result = json.loads(recognizer.FinalResult())
    transcript = re.sub(r"[^a-z ]", "", result.get("text", "").lower()).strip()
    letter = ALIASES.get(transcript)
    return {"transcript": transcript, "letter": letter, "recognized": letter is not None,
            "note": "Letter-name recognition only; not pronunciation scoring."}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path == "/api/health":
            return self.send_json(200, {"image": (IMAGE / "model.json").is_file() and (IMAGE / "weights.bin").is_file()
                         and (IMAGE / "metadata.json").is_file(), "speech": SPEECH.is_dir()})
        if path.startswith("/models/image/"):
            filename = path.removeprefix("/models/image/")
            if filename not in ("model.json", "metadata.json", "weights.bin"):
                return self.send_error(404)
            file = IMAGE / filename
            if not file.is_file():
                return self.send_error(404, "Missing image model file")
            data = file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json" if filename.endswith(".json") else "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/speech":
            return self.send_error(404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2_000_000:
                raise ValueError("Invalid recording size")
            result = analyze_audio(self.rfile.read(length))
            self.send_json(200, result)
        except (ValueError, wave.Error, RuntimeError, ImportError) as exc:
            self.send_json(422, {"error": str(exc)})
        except Exception as exc:
            self.send_json(500, {"error": f"Speech inference failed: {type(exc).__name__}"})

    def send_json(self, status, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"LetterStars: http://{HOST}:{PORT}")
    print("Image model:", IMAGE)
    print("Vosk model:", SPEECH)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
