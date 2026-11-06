"""LetterStars desktop application entrypoint."""
from letterstars.config import ROOT,APP_DATA,CONFIDENCE_THRESHOLD,STABLE_FRAMES,CAMERA_INDEX
from letterstars.adapters.audio import SystemVoice
from letterstars.adapters.camera import OpenCVCamera
from letterstars.adapters.image_model import TFLiteImageClassifier
from letterstars.adapters.speech_model import UnavailableSpeechClassifier
from letterstars.infrastructure.storage import SQLiteProgress
from letterstars.services.lesson import LessonService
from letterstars.ui.desktop import LetterStarsUI

def build_app():
    progress=SQLiteProgress(APP_DATA/"progress.db")
    image=TFLiteImageClassifier(ROOT/"models"/"image")
    lesson=LessonService(SystemVoice(),image,progress,UnavailableSpeechClassifier(),CONFIDENCE_THRESHOLD,STABLE_FRAMES)
    return LetterStarsUI(lesson,OpenCVCamera(CAMERA_INDEX),image)

if __name__=="__main__":
    build_app().run()
