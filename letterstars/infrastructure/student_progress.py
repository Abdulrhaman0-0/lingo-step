"""Per-child local progress. The child's stable ID is never inferred from the name."""
from datetime import datetime, timezone
from pathlib import Path
import secrets
import sqlite3
import uuid
from .storage import SQLiteProgress


class StudentProgressStore(SQLiteProgress):
    """SQLite repository with legacy-attempt migration and an offline sync outbox."""

    def __init__(self, path):
        super().__init__(path)
        self.active_student_id = None
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                pairing_code TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
            )""")
            columns = {row[1] for row in db.execute("PRAGMA table_info(attempts)")}
            if "student_id" not in columns:
                db.execute("ALTER TABLE attempts ADD COLUMN student_id TEXT")
            if "attempt_uuid" not in columns:
                db.execute("ALTER TABLE attempts ADD COLUMN attempt_uuid TEXT")
            if "synced_at" not in columns:
                db.execute("ALTER TABLE attempts ADD COLUMN synced_at TEXT")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_attempt_uuid ON attempts(attempt_uuid)")
            db.execute("CREATE INDEX IF NOT EXISTS ix_attempt_student ON attempts(student_id)")
            # Preserve pre-migration work, but never assign old attempts to a newly
            # created student. The explicit legacy profile keeps data separate.
            existing = db.execute("SELECT id FROM attempts WHERE student_id IS NULL").fetchall()
            if existing:
                db.execute("""INSERT OR IGNORE INTO students VALUES(?,?,?,?)""",
                           ("legacy", "سجل سابق", secrets.token_urlsafe(18),
                            datetime.now(timezone.utc).isoformat()))
                for (row_id,) in existing:
                    db.execute("UPDATE attempts SET student_id=?, attempt_uuid=? WHERE id=?",
                               ("legacy", str(uuid.uuid4()), row_id))

    def create_student(self, name):
        name = " ".join(str(name).strip().split())
        if not 1 <= len(name) <= 60:
            raise ValueError("Student name must be 1 to 60 characters")
        if any(ord(c) < 32 for c in name):
            raise ValueError("Invalid student name")
        student_id = str(uuid.uuid4())
        pair = secrets.token_urlsafe(18)
        with self._connect() as db:
            db.execute("INSERT INTO students VALUES(?,?,?,?)",
                       (student_id, name, pair, datetime.now(timezone.utc).isoformat()))
        self.active_student_id = student_id
        return student_id

    def students(self):
        with self._connect() as db:
            return [{"id": r[0], "name": r[1]}
                    for r in db.execute("SELECT student_id,name FROM students ORDER BY created_at DESC")]

    def select_student(self, student_id):
        with self._connect() as db:
            row = db.execute("SELECT student_id,name,pairing_code FROM students WHERE student_id=?",
                             (student_id,)).fetchone()
        if row is None:
            raise ValueError("Student does not exist")
        self.active_student_id = row[0]
        return {"id": row[0], "name": row[1], "pairing_code": row[2]}

    def current_student(self):
        if self.active_student_id is None:
            return None
        return self.select_student(self.active_student_id)

    def save(self, attempt):
        if not self.active_student_id:
            raise ValueError("Select a student before saving attempts")
        if attempt.result not in ("correct", "try_again"):
            raise ValueError("Only real evaluated attempts may be recorded")
        if attempt.mode not in ("learn", "revision"):
            raise ValueError("Invalid attempt mode")
        if attempt.target not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" or len(attempt.target) != 1:
            raise ValueError("Invalid target letter")
        event_id = str(uuid.uuid4())
        with self._connect() as db:
            db.execute("""INSERT INTO attempts
                (student_id,attempt_uuid,mode,target,observed,confidence,result,timestamp)
                VALUES(?,?,?,?,?,?,?,?)""",
                (self.active_student_id,event_id,attempt.mode,attempt.target,
                 attempt.observed,attempt.confidence,attempt.result,attempt.timestamp))
        return event_id

    def summary(self, student_id=None):
        student_id = student_id or self.active_student_id
        if student_id is None:
            return {"correct": 0, "try_again": 0, "total": 0, "learned": 0, "letters": []}
        with self._connect() as db:
            rows = db.execute(
                "SELECT result,COUNT(*) FROM attempts WHERE student_id=? GROUP BY result",
                (student_id,)).fetchall()
            letters = [x[0] for x in db.execute(
                """SELECT DISTINCT target FROM attempts WHERE student_id=?
                   AND result='correct' ORDER BY target""", (student_id,))]
        counts = dict(rows)
        return {"correct": counts.get("correct", 0), "try_again": counts.get("try_again", 0),
                "total": sum(counts.values()), "learned": len(letters), "letters": letters}

    def recent(self, limit=8, student_id=None):
        student_id = student_id or self.active_student_id
        if student_id is None:
            return []
        with self._connect() as db:
            return db.execute("""SELECT timestamp,mode,target,observed,result FROM attempts
                WHERE student_id=? ORDER BY id DESC LIMIT ?""",
                (student_id, max(0, min(int(limit), 100)))).fetchall()

    def pending_sync(self, limit=50):
        with self._connect() as db:
            rows = db.execute("""SELECT a.attempt_uuid,a.student_id,s.name,s.pairing_code,
                a.mode,a.target,a.observed,a.confidence,a.result,a.timestamp
                FROM attempts a JOIN students s ON s.student_id=a.student_id
                WHERE a.synced_at IS NULL ORDER BY a.id ASC LIMIT ?""",
                (max(1, min(int(limit), 100)),)).fetchall()
        return [{"id":r[0], "student_id":r[1], "student_name":r[2],
                 "pairing_code":r[3], "mode":r[4], "target":r[5],
                 "observed":r[6], "confidence":r[7], "result":r[8], "timestamp":r[9]}
                for r in rows]

    def mark_synced(self, event_ids):
        ids = list(event_ids)
        if not ids:
            return
        with self._connect() as db:
            db.executemany("UPDATE attempts SET synced_at=? WHERE attempt_uuid=?",
                           [(datetime.now(timezone.utc).isoformat(), i) for i in ids])
