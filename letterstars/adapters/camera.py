"""OpenCV USB camera adapter. Import is lazy so UI works without webcam."""
class OpenCVCamera:
    def __init__(self,index=0): self.index=index;self.cap=None
    def open(self):
        try: import cv2
        except ImportError as exc: raise RuntimeError("OpenCV not installed: pip install opencv-python") from exc
        self.cap=cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            self.close();raise RuntimeError("Camera unavailable: check USB and permissions")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
    def read(self):
        if self.cap is None: raise RuntimeError("Camera not open")
        ok,frame=self.cap.read()
        return frame if ok else None
    def close(self):
        if self.cap is not None: self.cap.release();self.cap=None
