"""LingoStep Raspberry Pi native Python entrypoint (no browser required)."""
import os
from letterstars.config import ROOT, APP_DATA, CONFIDENCE_THRESHOLD, STABLE_FRAMES, CAMERA_INDEX
from letterstars.adapters.audio import SystemVoice
from letterstars.adapters.camera import OpenCVCamera
from letterstars.adapters.image_model import TFLiteImageClassifier
from letterstars.adapters.vosk_speech import VoskSpeechClassifier
from letterstars.infrastructure.student_progress import StudentProgressStore
from letterstars.infrastructure.cloud_sync import CloudSync
from letterstars.infrastructure.cloud_settings import load_cloud_settings
from letterstars.services.lesson import LessonService
from letterstars.ui.final_ui import LingoStepApp


def build_app():
    load_cloud_settings(ROOT/"data/cloud-settings.json")
    progress = StudentProgressStore(APP_DATA/"progress.db")
    image = TFLiteImageClassifier(ROOT/"models"/"image")
    speech_path = os.getenv("LINGOSTEP_VOSK_MODEL", str(ROOT/"models"/"speech"/"vosk-model-small-en-us-0.15"))
    speech = VoskSpeechClassifier(speech_path)
    lesson = LessonService(SystemVoice(), image, progress, speech,
                           CONFIDENCE_THRESHOLD, STABLE_FRAMES)
    cloud = CloudSync(progress)
    return LingoStepApp(lesson, OpenCVCamera(CAMERA_INDEX), image,
                        progress, speech, cloud)


if __name__ == "__main__":
    build_app().run()
