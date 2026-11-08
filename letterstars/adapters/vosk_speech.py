"""Offline Vosk letter-name recognition on USB microphone.

Returns a Prediction using *observed* Vosk word confidences, never a
pronunciation-quality grade or a fabricated class probability.
"""
import json
import os
from pathlib import Path
import re
from ..domain.models import Prediction

LETTER_WORDS = {
    "a": "A", "ay": "A", "hey": "A",
    "b": "B", "bee": "B", "be": "B",
    "c": "C", "sea": "C", "see": "C",
    "d": "D", "dee": "D",
    "e": "E", "ee": "E",
    "f": "F", "eff": "F",
    "g": "G", "gee": "G",
    "h": "H", "aitch": "H", "age": "H",
    "i": "I", "eye": "I",
    "j": "J", "jay": "J",
    "k": "K", "kay": "K",
    "l": "L", "ell": "L", "el": "L",
    "m": "M", "em": "M",
    "n": "N", "en": "N",
    "o": "O", "oh": "O",
    "p": "P", "pee": "P",
    "q": "Q", "cue": "Q", "queue": "Q",
    "r": "R", "are": "R",
    "s": "S", "ess": "S",
    "t": "T", "tee": "T", "tea": "T",
    "u": "U", "you": "U",
    "v": "V", "vee": "V",
    "w": "W", "double you": "W", "double u": "W",
    "x": "X", "ex": "X",
    "y": "Y", "why": "Y",
    "z": "Z", "zee": "Z", "zed": "Z",
}


def parse_vosk_result(result):
    """Use word recognition evidence. Unknown and ambiguous transcripts return None."""
    transcript = re.sub(r"[^a-z ]", "", result.get("text", "").lower())
    transcript = " ".join(transcript.split())
    if not transcript:
        return None, transcript
    label = LETTER_WORDS.get(transcript)
    words = result.get("result", [])
    if label is None or not words:
        return None, transcript
    confidences = [float(w.get("conf", 0)) for w in words]
    if not confidences or any(not 0 <= x <= 1 for x in confidences):
        return None, transcript
    return Prediction(label, sum(confidences)/len(confidences), "real"), transcript


def microphone_rate(device=None, preferred=16000):
    """Use the requested rate if supported, otherwise the device's native rate."""
    import sounddevice as sd
    try:
        sd.check_input_settings(device=device, samplerate=preferred,
                                channels=1, dtype="int16")
        return preferred
    except sd.PortAudioError:
        native = int(sd.query_devices(device, "input")["default_samplerate"])
        sd.check_input_settings(device=device, samplerate=native,
                                channels=1, dtype="int16")
        return native


class VoskSpeechClassifier:
    def __init__(self, model_path, duration=2.5, rate=16000, device=None):
        self.model_path = Path(model_path)
        self.rate = int(rate)
        selection = device if device is not None else os.getenv("LINGOSTEP_MIC_DEVICE")
        if isinstance(selection, str) and selection.strip().isdigit():
            selection = int(selection.strip())
        self.device = selection
        self.duration = float(duration)
        self.model = None
        self.ready = False
        self.error = ""
        self.last_transcript = ""
        try:
            if not self.model_path.is_dir():
                raise FileNotFoundError("Vosk language model not installed")
            import vosk
            import sounddevice
            self.model = vosk.Model(str(self.model_path))
            self.ready = True
        except (ImportError, OSError, RuntimeError, FileNotFoundError) as exc:
            self.error = str(exc)

    def recognize_letter(self, audio=None):
        if not self.ready:
            raise RuntimeError("Vosk unavailable: " + self.error)
        import sounddevice as sd
        from vosk import KaldiRecognizer
        rate = self.rate
        # Tk UI calls this in a worker: capture must never freeze mainloop.
        if audio is None:
            rate = microphone_rate(self.device, self.rate)
            data = sd.rec(int(self.duration*rate), samplerate=rate,
                          channels=1, dtype="int16", device=self.device)
            sd.wait()
            pcm = data.tobytes()
        elif isinstance(audio, bytes):
            pcm = audio
        else:
            raise ValueError("Expected PCM16 bytes or microphone recording")
        # Tell Vosk the actual PCM rate, including 44.1/48 kHz USB recordings.
        rec = KaldiRecognizer(self.model, rate)
        rec.SetWords(True)
        rec.AcceptWaveform(pcm)
        result = json.loads(rec.FinalResult())
        prediction, self.last_transcript = parse_vosk_result(result)
        return prediction
