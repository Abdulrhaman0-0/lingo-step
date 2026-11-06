"""Camera-only hardware smoke test, independent from AI model."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from letterstars.adapters.camera import OpenCVCamera
camera=OpenCVCamera()
try:
    camera.open()
    frame=camera.read()
    if frame is None:raise RuntimeError("No frame read")
    print("Camera OK:",frame.shape)
finally:camera.close()
