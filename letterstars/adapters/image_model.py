"""Genuine TFLite inference; refuses to infer when files/runtime are missing.

Model metadata is explicit in models/image/config.json; never guess labels.
"""
from pathlib import Path
import json
from ..domain.models import Prediction

class TFLiteImageClassifier:
    def __init__(self, root):
        self.root=Path(root); self.interpreter=None; self.labels=[]
        self.ready=False;self.error="No trained image model installed"
        self._load()

    def _load(self):
        model=self.root/"model.tflite"
        config=self.root/"config.json"
        if not model.is_file() or not config.is_file(): return
        try:
            import numpy as np
            try:
                from tflite_runtime.interpreter import Interpreter
            except ImportError:
                from tensorflow.lite import Interpreter
            c=json.loads(config.read_text(encoding="utf-8"))
            labels=c["labels"]
            if not isinstance(labels,list) or len(labels)<2 or not all(isinstance(x,str) for x in labels):
                raise ValueError("Invalid labels in config.json")
            self.labels=labels
            self.means=float(c.get("input_mean",127.5))
            self.scales=float(c.get("input_std",127.5))
            self.channel_order=c.get("channel_order","RGB")
            self.interpreter=Interpreter(model_path=str(model),num_threads=2)
            self.interpreter.allocate_tensors()
            self.input=self.interpreter.get_input_details()[0]
            self.output=self.interpreter.get_output_details()[0]
            if self.input["shape"].size!=4: raise ValueError("Expected 4D image input")
            self.ready=True;self.error=""
        except Exception as exc:
            self.ready=False; self.error=f"Model loading failed: {exc}"

    def predict(self, frame):
        if not self.ready: return None
        import cv2
        import numpy as np
        _,height,width,channels=self.input["shape"]
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        image=cv2.resize(rgb,(int(width),int(height)))
        x=image.astype(np.float32)
        if self.input["dtype"]==np.float32:
            if self.scales==0: raise ValueError("input_std cannot be zero")
            x=(x-self.means)/self.scales
        elif self.input["dtype"]==np.uint8:
            x=image.astype(np.uint8)
        elif self.input["dtype"]==np.int8:
            # float preprocessing then quantize according to actual tensor metadata.
            scale,zero=self.input["quantization"]
            if scale<=0: raise ValueError("Invalid quantization scale")
            x=np.clip(np.round(((x-self.means)/self.scales)/scale+zero),-128,127).astype(np.int8)
        else:
            raise ValueError("Unsupported input tensor type")
        x=np.expand_dims(x,0)
        self.interpreter.set_tensor(self.input["index"],x)
        self.interpreter.invoke()
        raw=self.interpreter.get_tensor(self.output["index"])[0]
        scale,zero=self.output["quantization"]
        scores=(raw.astype(np.float32)-zero)*scale if scale>0 else raw.astype(np.float32)
        if len(scores)!=len(self.labels):
            raise ValueError("Output length does not match configured labels")
        best=int(np.argmax(scores))
        return Prediction(self.labels[best].strip().upper(),float(scores[best]),"real")
