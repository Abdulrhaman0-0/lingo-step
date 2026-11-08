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
        self.assertEqual(feedback.answer("try_again"), ("retry", "أحيه! حاول مرة أخرى"))
        self.assertEqual(feedback.answer("try_again"), ("retry_again", "يا نهار أسود! حاول مرة أخرى"))
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
                with patch("letterstars.adapters.audio.shutil.which", side_effect=lambda name: "/usr/bin/aplay" if name == "aplay" else None), \
                     patch("letterstars.adapters.audio.subprocess.Popen") as play:
                    play.return_value.communicate.return_value = (None, b"")
                    play.return_value.returncode = 0
                    voice.process = None
                    voice.say_feedback(key)
                    voice.wait()
                    self.assertEqual(play.call_args.args[0], ["/usr/bin/aplay", "-q", str(path)])

    def test_missing_output_error_is_reported_after_async_player_exits(self):
        voice = SystemVoice()
        voice.platform = "Linux"
        with patch("letterstars.adapters.audio.shutil.which", return_value="/usr/bin/aplay"), \
             patch("letterstars.adapters.audio.subprocess.Popen") as play:
            play.return_value.communicate.return_value = (None, b"aplay: audio open error: No such file or directory")
            play.return_value.returncode = 1
            voice.say_feedback("correct")
            with self.assertRaisesRegex(RuntimeError, "audio open error"):
                voice.wait()

    def test_explicit_output_device_is_used_for_feedback(self):
        with patch.dict("os.environ", {"LINGOSTEP_AUDIO_DEVICE": "plughw:CARD=Speaker,DEV=0"}):
            voice = SystemVoice()
        voice.platform = "Linux"
        with patch("letterstars.adapters.audio.shutil.which", return_value="/usr/bin/aplay"), \
             patch("letterstars.adapters.audio.subprocess.Popen") as play:
            play.return_value.communicate.return_value = (None, b"")
            play.return_value.returncode = 0
            voice.say_feedback("correct")
            voice.wait()
            self.assertIn("plughw:CARD=Speaker,DEV=0", play.call_args.args[0])

    def test_ui_reports_delayed_playback_errors(self):
        import queue
        app = LingoStepApp.__new__(LingoStepApp)
        app._thread_messages = queue.Queue()
        app.lesson = Mock()
        app.lesson.voice.pop_error.return_value = "No audio output device"
        app.root = Mock()
        app.render = Mock()
        with patch("builtins.print"):
            app.poll_workers()
        self.assertIn("الصوت لم يعمل", app.status)
        app.render.assert_called_once()

    def test_bluetooth_uses_desktop_player_before_hardware_alsa(self):
        voice = SystemVoice()
        voice.platform, voice.audio_device = "Linux", ""
        with patch("letterstars.adapters.audio.shutil.which", side_effect=lambda name: "/usr/bin/"+name):
            self.assertEqual(voice.playback_command("sound.wav"), ["/usr/bin/pw-play", "sound.wav"])
        with patch("letterstars.adapters.audio.shutil.which", side_effect=lambda name: "/usr/bin/"+name if name != "pw-play" else None):
            self.assertEqual(voice.playback_command("sound.wav"), ["/usr/bin/paplay", "sound.wav"])

    def test_letter_speech_uses_same_bluetooth_output_as_feedback(self):
        voice = SystemVoice()
        voice.platform, voice.audio_device, voice.command = "Linux", "", "/usr/bin/espeak-ng"
        with patch("letterstars.adapters.audio.shutil.which", side_effect=lambda name: "/usr/bin/pw-play" if name == "pw-play" else None), \
             patch("letterstars.adapters.audio.subprocess.Popen") as play:
            play.return_value.communicate.return_value = (None, b"")
            play.return_value.returncode = 0
            voice.say_letter("B")
            voice.wait()
            self.assertEqual(play.call_count, 2)
            synthesis, playback = [call.args[0] for call in play.call_args_list]
            self.assertIn("-w", synthesis)
            self.assertEqual(playback[0], "/usr/bin/pw-play")
            self.assertEqual(synthesis[synthesis.index("-w")+1], playback[1])

    def test_stop_during_synthesis_prevents_late_playback_into_microphone(self):
        import threading
        started, finished = threading.Event(), threading.Event()
        voice = SystemVoice()
        voice.platform, voice.audio_device, voice.command = "Linux", "", "/usr/bin/espeak-ng"
        proc = Mock()
        proc.poll.return_value = None
        proc.returncode = -15
        def communicate():
            started.set()
            self.assertTrue(finished.wait(3))
            return None, b"terminated"
        proc.communicate.side_effect = communicate
        proc.terminate.side_effect = finished.set
        with patch("letterstars.adapters.audio.subprocess.Popen", return_value=proc) as play:
            voice.say_letter("B")
            self.assertTrue(started.wait(3))
            voice.stop()
            voice.wait()
            play.assert_called_once()
            self.assertIsNone(voice.pop_error())
