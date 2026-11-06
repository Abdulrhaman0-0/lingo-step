"""SQLite repository, stored locally, no AI or GUI dependencies."""
import sqlite3
from pathlib import Path

class SQLiteProgress:
    def __init__(self, path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,target TEXT NOT NULL, observed TEXT,
                confidence REAL, result TEXT NOT NULL, timestamp TEXT NOT NULL
            )""")

    def _connect(self): return sqlite3.connect(str(self.path))

    def save(self,a):
        with self._connect() as db:
            db.execute("INSERT INTO attempts(mode,target,observed,confidence,result,timestamp) VALUES(?,?,?,?,?,?)",
                       (a.mode,a.target,a.observed,a.confidence,a.result,a.timestamp))

    def summary(self):
        with self._connect() as db:
            rows=db.execute("SELECT result,COUNT(*) FROM attempts GROUP BY result").fetchall()
        scores=dict(rows)
        return {"correct":scores.get("correct",0),"try_again":scores.get("try_again",0),
                "total":sum(scores.values())}

    def recent(self,limit=8):
        with self._connect() as db:
            rows=db.execute("SELECT timestamp,mode,target,observed,result FROM attempts ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return rows
