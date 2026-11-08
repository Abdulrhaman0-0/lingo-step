"""Run against the supplied model when optional camera/runtime packages exist."""
import unittest
from pathlib import Path
from unittest.mock import Mock

try:
    import cv2
    import numpy as np
    from ai_edge_litert.interpreter import Interpreter
    HAS_RUNTIME = True
except ImportError:
    HAS_RUNTIME = False

from letterstars.adapters.image_model import TFLiteImageClassifier
from letterstars.domain.models import Prediction
from letterstars.services.lesson import LessonService


@unittest.skipUnless(HAS_RUNTIME, "Install OpenCV, NumPy and LiteRT for model tests")
class FullModelRuntimeTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "models" / "image"
        self.model = TFLiteImageClassifier(root)
        self.assertTrue(self.model.ready, self.model.error)
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def test_real_model_loads_and_runs_with_27_classes(self):
        self.assertEqual(self.model.labels, list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["others"])
        self.assertEqual(list(self.model.input["shape"]), [1, 224, 224, 3])
        prediction = self.model.predict(self.frame)
        if prediction is not None:
            self.assertIn(prediction.label, list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
            self.assertTrue(0 <= prediction.confidence <= 1)

    def use_scores(self, winner, confidence):
        scores = np.zeros((1, 27), dtype=np.float32)
        scores[0, winner] = confidence
        scores[0, (winner + 1) % 27] = 1 - confidence
        self.model.interpreter = Mock()
        self.model.interpreter.get_tensor.return_value = scores

    def test_others_rejected_without_promoting_second_place(self):
        self.use_scores(26, 0.51)
        self.assertIsNone(self.model.predict(self.frame))

    def test_z_keeps_correct_output_index(self):
        self.use_scores(25, 0.95)
        prediction = self.model.predict(self.frame)
        self.assertEqual(prediction.label, "Z")
        self.assertAlmostEqual(prediction.confidence, 0.95)

    def test_background_clears_pending_frames_and_saves_no_attempt(self):
        self.use_scores(26, 0.99)
        store = Mock()
        lesson = LessonService(Mock(), self.model, store)
        lesson.frame_predictions.extend([Prediction("A", 0.99)] * 4)
        result, observed, confidence = lesson.check_frame(self.frame)
        self.assertEqual((result, observed, confidence), ("not_recognized", None, None))
        self.assertFalse(lesson.frame_predictions)
        self.assertFalse(lesson.save_image_result(result, observed, confidence))
        store.save.assert_not_called()
