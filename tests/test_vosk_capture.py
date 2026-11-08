import unittest
from unittest.mock import Mock, patch
from letterstars.adapters.vosk_speech import VoskSpeechClassifier, microphone_rate


class AudioError(Exception):
    pass


class VoskCaptureTests(unittest.TestCase):
    def fake_sounddevice(self):
        sd = Mock()
        sd.PortAudioError = AudioError
        sd.query_devices.return_value = {"default_samplerate": 48000.0, "name": "USB test mic"}
        return sd

    def test_supported_rate_is_kept(self):
        sd = self.fake_sounddevice()
        with patch.dict("sys.modules", {"sounddevice": sd}):
            self.assertEqual(microphone_rate(1), 16000)
        sd.query_devices.assert_not_called()

    def test_usb_native_rate_used_for_recording_and_vosk(self):
        sd = self.fake_sounddevice()
        sd.check_input_settings.side_effect = [AudioError("Invalid sample rate"), None]
        sd.rec.return_value.tobytes.return_value = b"\x10\x00" * 100
        vosk = Mock()
        vosk.KaldiRecognizer.return_value.AcceptWaveform.return_value = False
        vosk.KaldiRecognizer.return_value.FinalResult.return_value = '{"text":"bee","result":[{"conf":0.9}]}'
        speech = VoskSpeechClassifier.__new__(VoskSpeechClassifier)
        speech.ready, speech.model = True, object()
        speech.rate, speech.duration, speech.device = 16000, 2.5, 1
        with patch.dict("sys.modules", {"sounddevice": sd, "vosk": vosk}):
            self.assertEqual(speech.recognize_letter().label, "B")
        sd.rec.assert_called_once_with(120000, samplerate=48000, channels=1, dtype="int16", device=1)
        self.assertEqual(vosk.KaldiRecognizer.call_args.args[:2], (speech.model, 48000))
        import json
        grammar = json.loads(vosk.KaldiRecognizer.call_args.args[2])
        self.assertIn("bee", grammar)
        self.assertIn("zed", grammar)
        self.assertIn("[unk]", grammar)

    def test_external_pcm_keeps_declared_rate_without_querying_hardware(self):
        sd = self.fake_sounddevice()
        vosk = Mock()
        vosk.KaldiRecognizer.return_value.AcceptWaveform.return_value = False
        vosk.KaldiRecognizer.return_value.FinalResult.return_value = '{"text":""}'
        speech = VoskSpeechClassifier.__new__(VoskSpeechClassifier)
        speech.ready, speech.model, speech.rate = True, object(), 16000
        with patch.dict("sys.modules", {"sounddevice": sd, "vosk": vosk}):
            speech.recognize_letter(b"\0\0" * 100)
        sd.check_input_settings.assert_not_called()
        sd.rec.assert_not_called()
        self.assertEqual(vosk.KaldiRecognizer.call_args.args[:2], (speech.model, 16000))
        self.assertEqual(speech.last_issue, "quiet")

    def test_endpoint_result_is_not_lost_when_final_result_is_empty(self):
        sd = self.fake_sounddevice()
        vosk = Mock()
        rec = vosk.KaldiRecognizer.return_value
        rec.AcceptWaveform.return_value = True
        rec.Result.return_value = '{"text":"bee","result":[{"conf":0.9}]}'
        rec.FinalResult.return_value = '{"text":""}'
        speech = VoskSpeechClassifier.__new__(VoskSpeechClassifier)
        speech.ready, speech.model, speech.rate = True, object(), 16000
        with patch.dict("sys.modules", {"sounddevice": sd, "vosk": vosk}):
            self.assertEqual(speech.recognize_letter(b"\x10\x00" * 100).label, "B")

    def test_native_rate_error_is_reported(self):
        sd = self.fake_sounddevice()
        sd.check_input_settings.side_effect = AudioError("device unavailable")
        with patch.dict("sys.modules", {"sounddevice": sd}):
            with self.assertRaises(AudioError):
                microphone_rate(1)
