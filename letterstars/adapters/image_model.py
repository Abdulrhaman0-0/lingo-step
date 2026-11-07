"""Native Python LiteRT image inference adapter.

Needs a *converted and validated* models/image/model.tflite + config.json.
A Teachable Machine TensorFlow.js ZIP is NOT a TFLite model.
"""
import json
from pathlib import Path
from ..domain.models import Prediction


class TFLiteImageClassifier:
    def __init__(self, root):
        self.root=Path(root)
        self.ready=False
        self.error="لم يتم تثبيت نموذج الصور المحوّل (TFLite)"
        self.interpreter=None
        self.labels=[]
        self._load()

    def _load(self):
        model=self.root/"model.tflite"
        config=self.root/"config.json"
        if not model.is_file() or not config.is_file():
            return
        try:
            import numpy as np
            try:
                from ai_edge_litert.interpreter import Interpreter
            except ImportError:
                from tflite_runtime.interpreter import Interpreter
            c=json.loads(config.read_text(encoding="utf-8"))
            labels=c.get("labels")
            if labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
                raise ValueError("Image model labels must be exactly A-Z in output order")
            self.labels=labels
            self.mean=float(c.get("input_mean",127.5))
            self.std=float(c.get("input_std",127.5))
            if self.std==0:raise ValueError("input_std cannot be zero")
            self.channel_order=c.get("channel_order","RGB")
            if self.channel_order not in ("RGB","BGR","GRAY"):
                raise ValueError("Unexpected channel order")
            self.interpreter=Interpreter(model_path=str(model),num_threads=2)
            self.interpreter.allocate_tensors()
            self.input=self.interpreter.get_input_details()[0]
            self.output=self.interpreter.get_output_details()[0]
            shape=self.input["shape"]
            if len(shape)!=4 or shape[0]!=1 or shape[3] not in (1,3):
                raise ValueError("Expected 1xHxWx(1 or 3) input")
            self.ready=True
            self.error=""
        except Exception as exc:
            self.error=f"Image AI failed: {exc}"
            self.ready=False

    def predict(self, frame):
        if not self.ready:return None
        import cv2
        import numpy as np
        _,height,width,channels=self.input["shape"]
        if channels==1 or self.channel_order=="GRAY":
            image=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        elif self.channel_order=="RGB":
            image=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        else:
            image=frame
        image=cv2.resize(image,(int(width),int(height)))
        if channels==1:
            image=image.reshape(height,width,1)
        elif image.ndim==2:
            image=cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        if self.input["dtype"]==np.float32:
            x=(image.astype(np.float32)-self.mean)/self.std
        elif self.input["dtype"]==np.uint8:
            x=image.astype(np.uint8)
        elif self.input["dtype"]==np.int8:
            scale,zero=self.input["quantization"]
            if scale<=0:raise ValueError("Invalid quantization")
            x=np.clip(np.round(((image.astype(np.float32)-self.mean)/self.std)/scale+zero),
                      -128,127).astype(np.int8)
        else:
            raise ValueError("Unsupported input dtype")
        self.interpreter.set_tensor(self.input["index"],np.expand_dims(x,0))
        self.interpreter.invoke()
        raw=self.interpreter.get_tensor(self.output["index"])[0].reshape(-1)
        scale,zero=self.output["quantization"]
        scores=(raw.astype(np.float32)-zero)*scale if scale>0 else raw.astype(np.float32)
        if len(scores)!=26 or not np.all(np.isfinite(scores)):
            raise ValueError("Unexpected output scores")
        # This classifier expects a probability / softmax output, not logits.
        if float(np.min(scores)) < -0.001 or float(np.max(scores)) > 1.001 or abs(float(np.sum(scores))-1)>0.05:
            raise ValueError("Expected 26 probabilities; check model export / softmax")
        index=int(np.argmax(scores))
        return Prediction(self.labels[index],float(scores[index]),"real")
