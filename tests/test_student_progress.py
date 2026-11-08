import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from letterstars.domain.models import Attempt
from letterstars.infrastructure.student_progress import StudentProgressStore


class StudentProgressTests(unittest.TestCase):
    def test_short_codes_retry_collisions_and_pairing_resync_preserves_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=StudentProgressStore(Path(tmp)/"progress.db")
            with patch("letterstars.infrastructure.student_progress.new_pairing_code", side_effect=["ABCDEFGH","ABCDEFGH","JKLMNPQR"]):
                first=store.create_student("First")
                store.create_student("Second")
            self.assertEqual(store.current_student()["pairing_code"], "JKLMNPQR")
            store.select_student(first)
            store.save(Attempt.make("learn","A","A",.95,"correct"))
            event_id=store.pending_sync()[0]["id"]
            store.mark_synced([event_id])
            self.assertEqual(store.pending_sync(), [])
            store.requeue_pairing()
            self.assertEqual(store.pending_sync()[0]["id"], event_id)
            self.assertEqual(store.summary()["correct"], 1)

    def test_profiles_isolate_attempts_and_offline_outbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=StudentProgressStore(Path(tmp)/"progress.db")
            alice=db.create_student("سلمى")
            db.save(Attempt.make("revision","A","A",.93,"correct"))
            bob=db.create_student("أحمد")
            db.save(Attempt.make("revision","B","C",.90,"try_again"))
            self.assertNotEqual(alice,bob)
            db.select_student(alice)
            self.assertEqual(db.summary()["learned"],1)
            self.assertEqual(db.summary()["correct"],1)
            self.assertEqual(db.recent()[0][2],"A")
            db.select_student(bob)
            self.assertEqual(db.summary()["learned"],0)
            self.assertEqual(db.summary()["try_again"],1)
            unsynced=db.pending_sync()
            self.assertEqual(len(unsynced),2)
            self.assertNotEqual(unsynced[0]["pairing_code"],unsynced[1]["pairing_code"])
            db.mark_synced([unsynced[0]["id"]])
            self.assertEqual(len(db.pending_sync()),1)
            # Durable across reopening the database.
            reopened=StudentProgressStore(Path(tmp)/"progress.db")
            reopened.select_student(alice)
            self.assertEqual(reopened.summary()["correct"],1)

    def test_rejects_unselected_save_and_fake_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=StudentProgressStore(Path(tmp)/"progress.db")
            with self.assertRaises(ValueError):
                db.save(Attempt.make("learn","A","A",.99,"correct"))
            db.create_student("طفل")
            with self.assertRaises(ValueError):
                db.save(Attempt.make("learn","A","A",.99,"not_recognized"))

    def test_legacy_attempts_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            from letterstars.infrastructure.storage import SQLiteProgress
            path=Path(tmp)/"progress.db"
            old=SQLiteProgress(path)
            old.save(Attempt.make("revision","D","D",.98,"correct"))
            store=StudentProgressStore(path)
            self.assertIn("legacy",[s["id"] for s in store.students()])
            other=store.create_student("جديد")
            self.assertEqual(store.summary()["total"],0)
            store.select_student("legacy")
            self.assertEqual(store.summary()["total"],1)


if __name__=="__main__":
    unittest.main()
