"""Guardian website + authenticated, idempotent Pi upload API.

A separate Flask service: NEVER serves the child's Python Tkinter app.
Deploy behind HTTPS reverse proxy; do not expose localhost dev server publicly.
"""
from datetime import datetime, timezone
from functools import wraps
from contextlib import closing
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
from letterstars.domain.pairing import short_pairing_code

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for

HERE = Path(__file__).resolve().parent
USERNAME = re.compile(r"^[A-Za-z0-9_.-]{3,40}$")
LETTER = re.compile(r"^[A-Z]$")
STUDENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$"+salt.hex()+"$"+digest.hex()


def check_password(password, stored):
    try:
        algo,salt,digest = stored.split("$")
        if algo != "scrypt":
            return False
        actual=hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt),
                              n=2**14,r=8,p=1)
        return hmac.compare_digest(actual,bytes.fromhex(digest))
    except (ValueError,TypeError):
        return False


def connect(path):
    con=sqlite3.connect(path)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as db:
        db.executescript("""
          CREATE TABLE IF NOT EXISTS guardians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL
          );
          CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY, name TEXT NOT NULL, pair_hash TEXT NOT NULL
          );
          CREATE TABLE IF NOT EXISTS guardian_children (
            guardian_id INTEGER NOT NULL REFERENCES guardians(id),
            student_id TEXT NOT NULL REFERENCES students(student_id),
            PRIMARY KEY(guardian_id,student_id)
          );
          CREATE TABLE IF NOT EXISTS attempts (
            attempt_uuid TEXT PRIMARY KEY, student_id TEXT NOT NULL REFERENCES students(student_id),
            mode TEXT NOT NULL,target TEXT NOT NULL,observed TEXT,
            confidence REAL,result TEXT NOT NULL,timestamp TEXT NOT NULL
          );
          CREATE INDEX IF NOT EXISTS attempts_by_child ON attempts(student_id,timestamp);
        """)


def create_app(config=None):
    app=Flask(__name__,template_folder="templates",static_folder="static")
    app.config.update(
        SECRET_KEY=os.getenv("LINGOSTEP_SESSION_SECRET", ""),
        DEVICE_TOKEN=os.getenv("LINGOSTEP_DEVICE_TOKEN", ""),
        DB_PATH=os.getenv("LINGOSTEP_CLOUD_DB",str(HERE/"data"/"portal.db")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("LINGOSTEP_COOKIE_SECURE","1") != "0",
        MAX_CONTENT_LENGTH=1_000_000,
    )
    if config:
        app.config.update(config)
    if len(str(app.config["SECRET_KEY"])) < 32 or len(str(app.config["DEVICE_TOKEN"])) < 24:
        raise RuntimeError("Set LINGOSTEP_SESSION_SECRET (32+) and LINGOSTEP_DEVICE_TOKEN (24+) via environment.")
    initialize(app.config["DB_PATH"])

    def db():
        if "db" not in g:
            g.db=connect(app.config["DB_PATH"])
        return g.db

    @app.teardown_appcontext
    def close_db(_):
        conn=g.pop("db",None)
        if conn is not None:conn.close()

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["X-Frame-Options"]="DENY"
        response.headers["Referrer-Policy"]="no-referrer"
        if request.path.startswith(("/login","/register","/dashboard","/pair","/logout","/api/")):
            response.headers["Cache-Control"]="no-store"
        if request.is_secure:
            response.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
        return response

    @app.before_request
    def csrf_protection():
        if "_csrf" not in session:
            session["_csrf"]=secrets.token_urlsafe(24)
        if request.method == "POST" and not request.path.startswith("/api/"):
            if not hmac.compare_digest(session["_csrf"],request.form.get("csrf","")):
                abort(400,"CSRF validation failed")

    @app.context_processor
    def inject_csrf():
        return {"csrf_token":lambda:session["_csrf"]}

    def authorized(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            if not session.get("guardian_id"):
                return redirect(url_for("login"))
            return fn(*args,**kwargs)
        return wrapped

    @app.route("/")
    def index():
        return redirect(url_for("dashboard" if session.get("guardian_id") else "login"))

    @app.route("/register",methods=["GET","POST"])
    def register():
        if request.method=="POST":
            username=request.form.get("username","").strip()
            password=request.form.get("password","")
            if not USERNAME.fullmatch(username) or len(password)<12 or len(password)>256:
                flash("اسم الحساب 3–40 حرفًا إنجليزيًا، وكلمة المرور 12 حرفًا على الأقل.")
            else:
                try:
                    with db() as conn:
                        conn.execute("INSERT INTO guardians(username,password_hash) VALUES(?,?)",
                                     (username,hash_password(password)))
                    flash("تم إنشاء الحساب، سجّل الدخول الآن.")
                    return redirect(url_for("login"))
                except sqlite3.IntegrityError:
                    flash("اسم الحساب مستخدم بالفعل.")
        return render_template("account.html",mode="register")

    @app.route("/login",methods=["GET","POST"])
    def login():
        if request.method=="POST":
            username=request.form.get("username","").strip()
            password=request.form.get("password","")
            row=db().execute("SELECT id,password_hash FROM guardians WHERE username=?",
                             (username,)).fetchone()
            if row and check_password(password,row["password_hash"]):
                session.clear()
                session["guardian_id"]=row["id"]
                session["_csrf"]=secrets.token_urlsafe(24)
                return redirect(url_for("dashboard"))
            flash("بيانات الدخول غير صحيحة.")
        return render_template("account.html",mode="login")

    @app.route("/logout",methods=["POST"])
    @authorized
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/pair",methods=["POST"])
    @authorized
    def pair():
        code=request.form.get("code","").strip()
        if not 8<=len(code)<=100:
            flash("كود الربط غير صحيح.")
            return redirect(url_for("dashboard"))
        coded=hmac.new(app.config["SECRET_KEY"].encode(),short_pairing_code(code).encode(),hashlib.sha256).hexdigest()
        legacy=hmac.new(app.config["SECRET_KEY"].encode(),code.encode(),hashlib.sha256).hexdigest()
        matches=db().execute("SELECT student_id FROM students WHERE pair_hash IN (?,?)",(coded,legacy)).fetchall()
        row=matches[0] if len(matches)==1 else None
        if row is None:
            flash("كود الربط غير موجود. تأكد من مزامنة الجهاز أولًا.")
        else:
            with db() as conn:
                conn.execute("INSERT OR IGNORE INTO guardian_children VALUES(?,?)",
                             (session["guardian_id"],row["student_id"]))
            flash("تم ربط حساب الطفل.")
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    @authorized
    def dashboard():
        students=db().execute("""SELECT s.student_id,s.name FROM students s
            JOIN guardian_children gc ON gc.student_id=s.student_id
            WHERE gc.guardian_id=? ORDER BY name""",(session["guardian_id"],)).fetchall()
        selected=request.args.get("child","")
        ids={s["student_id"] for s in students}
        if selected not in ids:
            selected=students[0]["student_id"] if students else None
        stats=None; history=[]
        if selected:
            record=db().execute("""SELECT result,COUNT(*) n FROM attempts
                       WHERE student_id=? GROUP BY result""",(selected,)).fetchall()
            counts={r["result"]:r["n"] for r in record}
            letters=[r["target"] for r in db().execute("""SELECT DISTINCT target
                FROM attempts WHERE student_id=? AND result='correct'
                ORDER BY target""",(selected,))]
            history=db().execute("""SELECT timestamp,mode,target,observed,result FROM attempts
                WHERE student_id=? ORDER BY timestamp DESC LIMIT 12""",(selected,)).fetchall()
            correct=counts.get("correct",0)
            stats={"name":next(s["name"] for s in students if s["student_id"]==selected),
                   "correct":correct,"total":sum(counts.values()),
                   "try_again":counts.get("try_again",0),
                   "learned":len(letters),"letters":letters,
                   "achievements":[("أول حرف",correct>=1),
                                   ("بداية رائعة",correct>=5),
                                   ("متعلم سريع",correct>=10),
                                   ("أكملت الحروف",len(letters)>=26)]}
        return render_template("dashboard.html",students=students,selected=selected,
                               stats=stats,history=history,alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    @app.route("/api/v1/health")
    def health():
        return jsonify({"status":"ok"})

    @app.route("/api/v1/attempts",methods=["POST"])
    def ingest():
        token=request.headers.get("Authorization","")
        if not hmac.compare_digest(token,"Bearer "+app.config["DEVICE_TOKEN"]):
            abort(401)
        payload=request.get_json(silent=True)
        events=payload.get("events") if isinstance(payload,dict) else None
        if not isinstance(events,list) or len(events)>50:
            abort(400,"Expected up to 50 events")
        processed=[]
        # Validate all events first, before modifying the database.
        for item in events:
            if not isinstance(item,dict):
                abort(400)
            sid=item.get("student_id","")
            name=item.get("student_name","")
            code=item.get("pairing_code","")
            target=item.get("target","")
            observed=item.get("observed")
            value=item.get("confidence")
            if (not isinstance(sid,str) or not STUDENT_ID.fullmatch(sid) or
                not isinstance(name,str) or not 1<=len(name)<=60 or
                not isinstance(code,str) or not 8<=len(code)<=100 or
                item.get("mode") not in ("learn","revision") or
                not isinstance(target,str) or not LETTER.fullmatch(target) or
                (observed is not None and (not isinstance(observed,str) or
                   not LETTER.fullmatch(observed))) or
                item.get("result") not in ("correct","try_again") or
                not isinstance(value,(int,float)) or not 0<=value<=1 or
                not isinstance(item.get("id"),str) or not 10<=len(item["id"])<=80 or
                not isinstance(item.get("timestamp"),str) or not 10<=len(item["timestamp"])<=50):
                abort(400,"Invalid attempt")
            encoded=hmac.new(app.config["SECRET_KEY"].encode(),short_pairing_code(code).encode(),hashlib.sha256).hexdigest()
            legacy=hmac.new(app.config["SECRET_KEY"].encode(),code.encode(),hashlib.sha256).hexdigest()
            processed.append((item,encoded,legacy))
        accepted=[]
        with db() as conn:
            for item,encoded,legacy in processed:
                old=conn.execute("SELECT pair_hash FROM students WHERE student_id=?",
                                 (item["student_id"],)).fetchone()
                if old and not (hmac.compare_digest(old["pair_hash"],encoded) or hmac.compare_digest(old["pair_hash"],legacy)):
                    abort(403,"Student pairing credential mismatch")
                collision=conn.execute("SELECT student_id FROM students WHERE pair_hash=? AND student_id<>?",
                                       (encoded,item["student_id"])).fetchone()
                if collision:
                    abort(409,"Pairing code collision; keep the existing child's pairing credential")
                conn.execute("INSERT OR IGNORE INTO students VALUES(?,?,?)",
                             (item["student_id"],item["student_name"],encoded))
                if old:
                    conn.execute("UPDATE students SET pair_hash=? WHERE student_id=?",(encoded,item["student_id"]))
                existing=conn.execute("SELECT student_id FROM attempts WHERE attempt_uuid=?",
                                      (item["id"],)).fetchone()
                if existing and existing["student_id"]!=item["student_id"]:
                    abort(409,"Conflicting attempt ID")
                conn.execute("""INSERT OR IGNORE INTO attempts VALUES(?,?,?,?,?,?,?,?)""",
                             (item["id"],item["student_id"],item["mode"],
                              item["target"],item.get("observed"),item["confidence"],
                              item["result"],item["timestamp"]))
                accepted.append(item["id"])
        return jsonify({"accepted_ids":accepted})

    return app


if __name__=="__main__":
    app=create_app()
    app.run(host="127.0.0.1",port=8080)
