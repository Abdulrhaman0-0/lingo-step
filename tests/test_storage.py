import tempfile
import unittest
from pathlib import Path
from letterstars.domain.models import Attempt
from letterstars.infrastructure.storage import SQLiteProgress

class StorageTest(unittest.TestCase):
    def test_save_and_count(self):
        with tempfile.TemporaryDirectory() as temp:
            db=SQLiteProgress(Path(temp)/"progress.db")
            self.assertEqual(db.summary()["total"],0)
            db.save(Attempt.make("revision","A","A",0.98,"correct"))
            self.assertEqual(db.summary()["correct"],1)
            self.assertEqual(len(db.recent()),1)

if __name__=="__main__": unittest.main()
