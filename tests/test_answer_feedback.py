import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

from letterstars.services.feedback import AnswerFeedback, PHRASES
from letterstars.adapters.audio import SystemVoice
from letterstars.ui.final_ui import LingoStepApp


class AnswerFeedbackTests(unittest.TestCase):
    def test_wrong_answers_escalate_until_correct_then_restart(self):
        feedback = AnswerFeedback()
        self.assertEqual(feedback.answer("try_again"), ("retry", "حاول مرة أخرى"))
        self.assertEqual(feedback.answer("try_again"), ("retry_again", "محاولة خاطئة، جرب ثانيةً"))
        self.assertEqual(feedback.answer("try_again")[0], "retry_again")
        self.assertEqual(feedback.answer("correct"), ("correct", "ممتاز"))
        self.assertEqual(feedback.answer("try_again")[0], "retry")

    def test_unknown_audio_or_background_does_not_count_as_wrong(self):
        feedback = AnswerFeedback()
        for result in ("not_recognized", "unsupported_letter", "unavailable"):
            self.assertIsNone(feedback.answer(result))
        self.assertEqual(feedback.answer("try_again")[0], "retry")

    def test_new_activity_resets_wrong_attempts(self):
        feedback = AnswerFeedback()
        feedback.answer("try_again")
        feedback.reset()
        self.assertEqual(feedback.answer("try_again")[0], "retry")

    def test_ui_plays_the_phrase_and_surfaces_playback_failure(self):
        app = LingoStepApp.__new__(LingoStepApp)
        app.feedback = AnswerFeedback()
        app.lesson = Mock()
        app.answer_feedback("try_again")
        self.assertEqual(app.status, PHRASES["retry"])
        app.lesson.voice.say_feedback.assert_called_once_with("retry")
        app.lesson.voice.say_feedback.side_effect = OSError("No speaker")
        app.answer_feedback("correct")
        self.assertIn("ممتاز", app.status)
        self.assertIn("No speaker", app.status)

    def test_clips_are_real_pcm_and_play_without_tts_or_network(self):
        root = Path(__file__).resolve().parents[1] / "assets" / "audio"
        voice = SystemVoice()
        voice.platform = "Linux"
        for key in PHRASES:
            with self.subTest(key=key):
                path = root / (key + ".wav")
                with wave.open(str(path), "rb") as clip:
                    self.assertEqual(clip.getsampwidth(), 2)
                    self.assertGreater(clip.getnframes(), 0)
                    self.assertTrue(any(clip.readframes(clip.getnframes())))
                with patch("letterstars.adapters.audio.shutil.which", return_value="/usr/bin/aplay"), \
                     patch("letterstars.adapters.audio.subprocess.Popen") as play:
                    voice.process = None
                    voice.say_feedback(key)
                    self.assertEqual(play.call_args.args[0], ["/usr/bin/aplay", "-q", str(path)])
