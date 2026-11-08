"""Real TFLite image model adapter used by the native Python UI.

Accepted labels: a contiguous A..N subset, all A..Z, or A..Z + others.
For a target letter outside the installed model's classes, the lesson
refuses to save any revision prediction.
"""
import json
from pathlib import Path
from ..domain.models import Prediction

ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def validate_labels(labels):
    if labels == ALPHABET + ["others"]:
        return labels
    if not isinstance(labels, list) or len(labels) < 2 or len(labels) > 26:
        raise ValueError("Expected 2..26 letter labels")
    if labels != ALPHABET[:len(labels)]:
        raise ValueError("Model labels must be uppercase A..N, in model output order")
    return labels


class TFLiteImageClassifier:
    def __init__(self, root):
        self.root = Path(root)
        self.interpreter = None
        self.labels = []
        self.ready = False
        self.error = "نموذج الصور غير مثبت"
        self._load()

    def _load(self):
        model = self.root / "model.tflite"
        config = self.root / "config.json"
        if not model.is_file() or not config.is_file():
            return
        try:
            import numpy as np
            try:
                from ai_edge_litert.interpreter import Interpreter
            except ImportError:
                try:
                    from tflite_runtime.interpreter import Interpreter
                except ImportError:
                    from tensorflow.lite import Interpreter
            options = json.loads(config.read_text(encoding="utf-8"))
            self.labels = validate_labels(options["labels"])
            self.mean = float(options.get("input_mean", 127.5))
            self.std = float(options.get("input_std", 127.5))
            self.channel_order = options.get("channel_order", "RGB")
            if self.std == 0 or self.channel_order not in ("RGB", "BGR", "GRAY"):
                raise ValueError("Invalid input normalization or channel order")
            self.interpreter = Interpreter(model_path=str(model), num_threads=2)
            self.interpreter.allocate_tensors()
            self.input = self.interpreter.get_input_details()[0]
            self.output = self.interpreter.get_output_details()[0]
            shape = self.input["shape"]
            if len(shape) != 4 or shape[0] != 1 or shape[3] not in (1, 3):
                raise ValueError("Expected 1xHxWx(1 or 3) model input")
            output_shape = self.output["shape"]
            if int(np.prod(output_shape)) != len(self.labels):
                raise ValueError(
                    f"Output has {int(np.prod(output_shape))} values, but config lists {len(self.labels)} letters"
                )
            self.ready = True
            self.error = ""
        except Exception as exc:
            self.ready = False
            self.error = f"Image AI failed: {exc}"

    def supports_letter(self, letter):
        return self.ready and letter in self.labels

    def predict(self, frame):
        if not self.ready:
            return None
        import cv2
        import numpy as np

        _, height, width, channels = self.input["shape"]
        if channels == 1 or self.channel_order == "GRAY":
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif self.channel_order == "RGB":
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            image = frame
        image = cv2.resize(image, (int(width), int(height)))
        if channels == 1:
            image = image.reshape(height, width, 1)
        elif image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        if self.input["dtype"] == np.float32:
            x = (image.astype(np.float32) - self.mean) / self.std
        elif self.input["dtype"] == np.uint8:
            x = image.astype(np.uint8)
        elif self.input["dtype"] == np.int8:
            scale, zero = self.input["quantization"]
            if scale <= 0:
                raise ValueError("Invalid input quantization scale")
            x = np.clip(np.round(((image.astype(np.float32) - self.mean)/self.std)/scale + zero),
                        -128, 127).astype(np.int8)
        else:
            raise ValueError("Unsupported input dtype")

        self.interpreter.set_tensor(self.input["index"], np.expand_dims(x, 0))
        self.interpreter.invoke()
        raw = self.interpreter.get_tensor(self.output["index"]).reshape(-1)
        scale, zero = self.output["quantization"]
        scores = (raw.astype(np.float32) - zero)*scale if scale > 0 else raw.astype(np.float32)
        if len(scores) != len(self.labels) or not np.all(np.isfinite(scores)):
            raise ValueError("Model output scores mismatch configured labels")
        if (np.min(scores) < -0.001 or np.max(scores) > 1.001
                or abs(float(np.sum(scores)) - 1) > .05):
            raise ValueError("Expected normalized probabilities, not logits")
        best = int(np.argmax(scores))
        # Reject background/unknown input; never promote the runner-up letter.
        if self.labels[best] == "others":
            return None
        return Prediction(self.labels[best], float(scores[best]), "real")
