from pathlib import Path
import tempfile
import unittest

from scripts.run_demo import demo_settings


class DemoSettingsTests(unittest.TestCase):
    def test_keys_survive_restart_so_pairing_remains_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"data/demo-settings.json"
            first = demo_settings(path)
            self.assertGreaterEqual(len(first["session_secret"]), 32)
            self.assertGreaterEqual(len(first["device_token"]), 24)
            self.assertEqual(demo_settings(path), first)

    def test_corrupt_settings_are_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"demo-settings.json"
            path.write_text('{"device_token":"short"}', encoding="utf-8")
            before = path.read_text()
            with self.assertRaises(ValueError):
                demo_settings(path)
            self.assertEqual(path.read_text(), before)
