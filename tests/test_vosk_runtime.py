"""Real Vosk tests on synthetic English speech, not microphone acceptance tests."""
from pathlib import Path
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models/speech/vosk-model-small-en-us-0.15"
try:
    import vosk
    import sounddevice
    HAS_RUNTIME = MODEL.is_dir()
except ImportError:
    HAS_RUNTIME = False

from letterstars.adapters.vosk_speech import VoskSpeechClassifier


@unittest.skipUnless(HAS_RUNTIME, "Install Vosk, sounddevice and the English model")
class VoskRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        vosk.SetLogLevel(-1)
        cls.speech = VoskSpeechClassifier(MODEL)
        if not cls.speech.ready:
            raise RuntimeError(cls.speech.error)

    def recognize(self, name):
        with wave.open(str(ROOT/"tests/fixtures"/name), "rb") as source:
            self.speech.rate = source.getframerate()
            return self.speech.recognize_letter(source.readframes(source.getnframes()))

    def test_known_letter_audio_passes_lesson_confidence_threshold(self):
        for label in ("B", "C", "Z"):
            with self.subTest(label=label):
                prediction = self.recognize("letter_"+label.lower()+".wav")
                self.assertIsNotNone(prediction, self.speech.last_transcript)
                self.assertEqual(prediction.label, label)
                self.assertGreaterEqual(prediction.confidence, .65)

    def test_unrelated_speech_is_not_forced_into_a_letter(self):
        self.assertIsNone(self.recognize("unrelated.wav"))

    def test_silent_audio_is_reported_as_quiet(self):
        self.speech.rate = 16000
        self.assertIsNone(self.speech.recognize_letter(bytes(16000*2*4)))
        self.assertEqual(self.speech.last_issue, "quiet")
