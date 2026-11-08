import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from letterstars.domain.models import Attempt
from letterstars.infrastructure.cloud_sync import CloudSync, allowed_cloud_url
from letterstars.infrastructure.student_progress import StudentProgressStore


class Response:
    status=200
    def __init__(self,ids):
        self.body=json.dumps({"accepted_ids":ids}).encode()
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def read(self,n):return self.body[:n]


class CloudOutboxTest(unittest.TestCase):
    def test_https_validation_and_retry(self):
        self.assertFalse(allowed_cloud_url("http://remote.example"))
        self.assertTrue(allowed_cloud_url("https://cloud.example"))
        self.assertTrue(allowed_cloud_url("http://127.0.0.1:8080"))
        with tempfile.TemporaryDirectory() as tmp:
            store=StudentProgressStore(Path(tmp)/"db.sqlite")
            store.create_student("سلمى")
            store.save(Attempt.make("revision","A","A",0.9,"correct"))
            event_id=store.pending_sync()[0]["id"]
            client=CloudSync(store,"https://cloud.example","token")
            with patch("letterstars.infrastructure.cloud_sync.urlopen",side_effect=TimeoutError):
                self.assertEqual(client.sync_once(),0)
            self.assertEqual(len(store.pending_sync()),1)
            with patch("letterstars.infrastructure.cloud_sync.urlopen",return_value=Response([event_id])):
                self.assertEqual(client.sync_once(),1)
            self.assertEqual(store.pending_sync(),[])
            self.assertEqual(client.sync_once(),0)


if __name__=="__main__":
    unittest.main()
