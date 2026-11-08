"""Offline Vosk letter-name recognition on USB microphone.

Returns a Prediction using *observed* Vosk word confidences, never a
pronunciation-quality grade or a fabricated class probability.
"""
import json
import os
from pathlib import Path
import re
from array import array
import math
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

# One spelling per pronunciation avoids splitting Vosk's word confidence over
# homophones (e.g. bee/be/b). Both distinct Z pronunciations are supported.
LETTER_GRAMMAR = [
    "a", "bee", "see", "dee", "e", "eff", "gee", "h", "eye", "jay",
    "kay", "el", "em", "n", "oh", "pee", "queue", "are", "ess", "tee",
    "you", "vee", "double you", "ex", "why", "zee", "zed", "[unk]",
]


def parse_vosk_result(result):
    """Use word recognition evidence. Unknown and ambiguous transcripts return None."""
    transcript = re.sub(r"[^a-z ]", "", result.get("text", "").lower())
    transcript = " ".join(transcript.split())
    if not transcript:
        return None, transcript
    label = LETTER_WORDS.get(transcript)
    if label is None:
        # Repeating the same letter is fine; mixed letters remain ambiguous.
        repeated = [LETTER_WORDS.get(word) for word in transcript.split()]
        if repeated and None not in repeated and len(set(repeated)) == 1:
            label = repeated[0]
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
    def __init__(self, model_path, duration=4.0, rate=16000, device=None):
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
        self.last_audio_rms = 0.0
        self.last_audio_peak = 0
        self.last_sample_rate = self.rate
        self.last_device_name = ""
        self.last_issue = ""
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
        self.last_transcript = ""
        self.last_issue = ""
        # Tk UI calls this in a worker: capture must never freeze mainloop.
        if audio is None:
            rate = microphone_rate(self.device, self.rate)
            self.last_device_name = sd.query_devices(self.device, "input")["name"]
            data = sd.rec(int(self.duration*rate), samplerate=rate,
                          channels=1, dtype="int16", device=self.device)
            sd.wait()
            pcm = data.tobytes()
        elif isinstance(audio, bytes):
            pcm = audio
        else:
            raise ValueError("Expected PCM16 bytes or microphone recording")
        samples = array("h")
        samples.frombytes(pcm)
        self.last_sample_rate = rate
        self.last_audio_peak = max((abs(x) for x in samples), default=0)
        self.last_audio_rms = math.sqrt(sum(x*x for x in samples)/len(samples)) if samples else 0.0
        # All letters are candidates, never only the expected target. [unk]
        # allows unrelated speech to be rejected instead of forced into a letter.
        grammar = json.dumps(LETTER_GRAMMAR)
        rec = KaldiRecognizer(self.model, rate, grammar)
        rec.SetWords(True)
        results = []
        for start in range(0, len(pcm), 8000):
            if rec.AcceptWaveform(pcm[start:start+8000]):
                results.append(json.loads(rec.Result()))
        results.append(json.loads(rec.FinalResult()))
        result = {"text": " ".join(r.get("text", "") for r in results).strip(),
                  "result": [word for r in results for word in r.get("result", [])]}
        prediction, self.last_transcript = parse_vosk_result(result)
        if prediction is None:
            self.last_issue = "quiet" if self.last_audio_rms < 30 else "unrecognized"
        return prediction
