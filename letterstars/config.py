from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
APP_DATA=Path(os.environ.get("LETTERSTARS_DATA_DIR",str(ROOT/"data")))
CONFIDENCE_THRESHOLD=0.80
STABLE_FRAMES=5
CAMERA_INDEX=int(os.environ.get("LETTERSTARS_CAMERA","0"))
