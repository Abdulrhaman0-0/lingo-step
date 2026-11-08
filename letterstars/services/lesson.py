"""Hardware-independent lesson and evaluation use cases."""
from collections import deque
from ..domain.models import LETTERS, Attempt
from ..domain.evaluation import decide


class LessonService:
    def __init__(self, voice, image_model, progress, speech_model=None,
                 threshold=0.80, stable_frames=5, speech_threshold=0.65):
        self.voice = voice
        self.image_model = image_model
        self.progress = progress
        self.speech_model = speech_model
        self.threshold = float(threshold)
        self.speech_threshold = float(speech_threshold)
        self.stable_frames = int(stable_frames)
        self.target = "A"
        self.frame_predictions = deque(maxlen=stable_frames)

    def select(self, letter):
        if letter not in LETTERS:
            raise ValueError("Invalid letter")
        self.target = letter
        self.frame_predictions.clear()

    def speak(self):
        self.voice.say_letter(self.target)

    def check_frame(self, frame):
        # Never grade a target outside the trained model's class set.
        if self.image_model.ready and self.target not in self.image_model.labels:
            self.frame_predictions.clear()
            return "unsupported_letter", None, None
        prediction = self.image_model.predict(frame)
        if prediction is None:
            self.frame_predictions.clear()
            return "not_recognized", None, None
        self.frame_predictions.append(prediction)
        result, observed = decide(self.target, self.frame_predictions,
                                  self.threshold, self.stable_frames)
        return result, observed, prediction.confidence

    def save_image_result(self, result, observed, confidence):
        if result not in ("correct", "try_again"):
            return False
        self.progress.save(Attempt.make("revision", self.target, observed, confidence, result))
        self.frame_predictions.clear()
        return True

    def check_speech(self, audio=None):
        if self.speech_model is None:
            return "unavailable", None
        # Vosk confidence estimates the transcription, not pronunciation quality.
        prediction = self.speech_model.recognize_letter(audio)
        if (prediction is None or prediction.source != "real" or
                not 0 <= prediction.confidence <= 1 or
                prediction.confidence < self.speech_threshold):
            return "not_recognized", prediction
        result = "correct" if prediction.label.upper() == self.target else "try_again"
        self.progress.save(Attempt.make("learn", self.target, prediction.label,
                                        prediction.confidence, result))
        return result, prediction
