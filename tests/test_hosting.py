import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from cloud.hosting import prepare_settings, create_hosted_app
from letterstars.infrastructure.cloud_settings import load_cloud_settings
from letterstars.infrastructure.student_progress import StudentProgressStore
from letterstars.domain.models import Attempt
from scripts.configure_cloud import save_connection
from scripts.build_web_bundle import build_bundle


class HostingTests(unittest.TestCase):
    def test_host_keys_and_database_survive_setup_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = prepare_settings(tmp, "https://example.pythonanywhere.com")
            app = create_hosted_app(tmp)
            self.assertTrue(app.config["SESSION_COOKIE_SECURE"])
            self.assertEqual(app.test_client().get("/api/v1/health").json, {"status":"ok"})
            again = prepare_settings(tmp, "https://example.pythonanywhere.com")
            self.assertEqual(settings, again)
            self.assertTrue((Path(tmp)/"portal.db").exists())

    def test_pi_saves_connection_requeues_once_and_preserves_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            store=StudentProgressStore(root/"progress.db")
            store.create_student("Hosting Test")
            store.save(Attempt.make("learn","A","A",.95,"correct"))
            event=store.pending_sync()[0]["id"]
            store.mark_synced([event])
            connection={"url":"https://example.pythonanywhere.com","token":"t"*40}
            (root/"source.json").write_text(json.dumps(connection))
            save_connection(root/"source.json",root/"saved.json",store.path)
            self.assertEqual(store.pending_sync()[0]["id"], event)
            store.mark_synced([event])
            save_connection(root/"source.json",root/"saved.json",store.path)
            self.assertEqual(store.pending_sync(), [])
            self.assertEqual(store.summary()["correct"], 1)
            with patch.dict(os.environ, {}, clear=True):
                load_cloud_settings(root/"saved.json")
                self.assertEqual(os.environ["LINGOSTEP_DEVICE_TOKEN"], "t"*40)
            with patch.dict(os.environ, {"LINGOSTEP_CLOUD_URL":"http://127.0.0.1:8080", "LINGOSTEP_DEVICE_TOKEN":"demo"},clear=True):
                load_cloud_settings(root/"saved.json")
                self.assertEqual(os.environ["LINGOSTEP_DEVICE_TOKEN"], "demo")

    def test_bad_connection_does_not_replace_existing_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"saved.json").write_text("original")
            (root/"bad.json").write_text(json.dumps({"url":"http://remote.example","token":"x"*40}))
            with self.assertRaises(ValueError):
                save_connection(root/"bad.json",root/"saved.json",root/"progress.db")
            self.assertEqual((root/"saved.json").read_text(), "original")

    def test_web_bundle_excludes_models_and_private_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=build_bundle(Path(tmp)/"web.zip")
            with ZipFile(output) as archive:
                names=archive.namelist()
                self.assertIn("lingostep-web/cloud/portal.py",names)
                self.assertIn("lingostep-web/letterstars/domain/pairing.py",names)
                self.assertFalse(any("/data/" in p or ".venv" in p or "/models/" in p or p.endswith(".db") for p in names))
