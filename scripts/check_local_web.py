"""Check local device-to-guardian flow using temporary databases and test data."""
import argparse
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--speech-wav", type=Path, help="Optional mono PCM16 recording to test real Vosk instead of a synthetic attempt")
    parser.add_argument("--target", default="B", choices=list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    args = parser.parse_args()
    from werkzeug.serving import make_server, WSGIRequestHandler
    from cloud.portal import create_app
    from letterstars.domain.models import Attempt
    from letterstars.infrastructure.student_progress import StudentProgressStore
    from letterstars.infrastructure.cloud_sync import CloudSync

    class QuietHandler(WSGIRequestHandler):
        def log(self, *args, **kwargs):
            pass

    with tempfile.TemporaryDirectory(prefix="lingostep-web-check-") as tmp:
        token = secrets.token_urlsafe(32)
        app = create_app({"TESTING": True, "DB_PATH": str(Path(tmp)/"cloud.db"),
                          "SECRET_KEY": secrets.token_urlsafe(48), "DEVICE_TOKEN": token,
                          "SESSION_COOKIE_SECURE": False})
        server = make_server("127.0.0.1", 0, app, request_handler=QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            store = StudentProgressStore(Path(tmp)/"device.db")
            store.create_student("Local Integration Test")
            if args.speech_wav:
                from letterstars.adapters.vosk_speech import VoskSpeechClassifier
                from letterstars.services.lesson import LessonService
                with wave.open(str(args.speech_wav), "rb") as source:
                    if source.getnchannels() != 1 or source.getsampwidth() != 2:
                        raise ValueError("Use mono PCM16 WAV")
                    speech = VoskSpeechClassifier(ROOT/"models/speech/vosk-model-small-en-us-0.15", rate=source.getframerate())
                    lesson = LessonService(None, None, store, speech_model=speech)
                    lesson.select(args.target)
                    result, prediction = lesson.check_speech(source.readframes(source.getnframes()))
                if result != "correct":
                    raise RuntimeError(f"Speech did not match {args.target}: {result}, {prediction}")
                print("Real Vosk -> evaluated lesson -> local student record: PASS")
            else:
                store.save(Attempt.make("learn", args.target, args.target, .95, "correct"))
                print("Using synthetic test attempt; this does not test speech recognition.")
            sync = CloudSync(store, f"http://127.0.0.1:{server.server_port}", token)
            if sync.sync_once() != 1 or store.pending_sync():
                raise RuntimeError("HTTP sync failed: " + sync.last_error)
            client = app.test_client()

            def post(path, fields):
                client.get("/login")
                with client.session_transaction() as session:
                    fields = dict(fields, csrf=session["_csrf"])
                return client.post(path, data=fields, follow_redirects=True)

            credentials = {"username": "local_test_guardian", "password": secrets.token_urlsafe(32)}
            post("/register", credentials)
            post("/login", credentials)
            with client.session_transaction() as session:
                if "guardian_id" not in session:
                    raise RuntimeError("Guardian registration/login failed")
            post("/pair", {"code": store.current_student()["pairing_code"]})
            dashboard = client.get("/dashboard").get_data(as_text=True)
            if "Local Integration Test" not in dashboard or "1 / 26" not in dashboard:
                raise RuntimeError("Paired child progress missing from dashboard")
            if sync.sync_once() != 0:
                raise RuntimeError("Repeated sync should not upload another attempt")
            print("PASS: local HTTP upload, guardian registration/login, pairing, dashboard 1/26, no duplicate sync.")
            print("Temporary test data removed on exit. Hosting/HTTPS and actual Pi networking are separate checks.")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    main()
