import json
from pathlib import Path
import tempfile
import unittest
from cloud.portal import create_app


class ParentCloudTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.token="t"*48
        self.app=create_app({"TESTING":True,
                             "DB_PATH":str(Path(self.tmp.name)/"cloud.db"),
                             "SECRET_KEY":"s"*64,
                             "DEVICE_TOKEN":self.token,
                             "SESSION_COOKIE_SECURE":False})
        self.client=self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def post_form(self,path,data,client=None):
        client=client or self.client
        with client.session_transaction() as sess:
            token=sess.get("_csrf")
        if not token:
            client.get("/login")
            with client.session_transaction() as sess:token=sess["_csrf"]
        return client.post(path,data=dict(data,csrf=token),follow_redirects=True)

    def test_private_dashboard_idempotent_upload_and_pairing(self):
        r=self.client.post("/api/v1/attempts",json={"events":[]})
        self.assertEqual(r.status_code,401)
        event={"id":"attempt-123456789","student_id":"student-1234",
               "student_name":"طفل تجريبي","pairing_code":"secret123456789012345678",
               "mode":"revision","target":"A","observed":"A",
               "confidence":.95,"result":"correct","timestamp":"2026-11-08T12:00:00Z"}
        headers={"Authorization":"Bearer "+self.token}
        for _ in range(2):
            result=self.client.post("/api/v1/attempts",json={"events":[event]},headers=headers)
            self.assertEqual(result.status_code,200,result.data)
            self.assertEqual(result.json["accepted_ids"],[event["id"]])
        self.client.get("/register")
        self.post_form("/register",{"username":"guardian1","password":"passphrase-strong-123"})
        self.post_form("/login",{"username":"guardian1","password":"passphrase-strong-123"})
        before=self.client.get("/dashboard")
        self.assertNotIn("طفل تجريبي",before.get_data(as_text=True))
        self.post_form("/pair",{"code":"secret123456789012345678"})
        shown=self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("طفل تجريبي",shown)
        self.assertIn("1 / 26",shown)
        # A different authenticated guardian must never read another child's results.
        other=self.app.test_client()
        other.get("/register")
        self.post_form("/register",{"username":"guardian2","password":"passphrase-strong-456"},other)
        self.post_form("/login",{"username":"guardian2","password":"passphrase-strong-456"},other)
        self.assertNotIn("طفل تجريبي",other.get("/dashboard?child=student-1234").get_data(as_text=True))

    def test_pair_needs_csrf_and_secret(self):
        self.client.get("/register")
        invalid=self.client.post("/register",data={"username":"a","password":"passwordpassword"})
        self.assertEqual(invalid.status_code,400)
        r=self.client.post("/api/v1/attempts",json={"events":[{"id":"x"}]},
                           headers={"Authorization":"Bearer "+self.token})
        self.assertEqual(r.status_code,400)

    def test_old_record_upgrades_to_short_code_without_losing_link_or_double_counting(self):
        import hashlib, hmac
        from contextlib import closing
        from cloud.portal import connect
        old_code="AbCdE9_x-long-legacy-secret"
        event={"id":"short-code-attempt-1","student_id":"short-code-child",
               "student_name":"Short Code Child","pairing_code":old_code,
               "mode":"learn","target":"B","observed":"B","confidence":.95,
               "result":"correct","timestamp":"2026-11-09T12:00:00Z"}
        old_hash=hmac.new(self.app.config["SECRET_KEY"].encode(),old_code.encode(),hashlib.sha256).hexdigest()
        with closing(connect(self.app.config["DB_PATH"])) as db:
            with db:
                db.execute("INSERT INTO students VALUES(?,?,?)",(event["student_id"],event["student_name"],old_hash))
        self.post_form("/register",{"username":"short_parent","password":"strong-passphrase-123"})
        self.post_form("/login",{"username":"short_parent","password":"strong-passphrase-123"})
        self.post_form("/pair",{"code":old_code})
        headers={"Authorization":"Bearer "+self.token}
        for _ in range(2):
            response=self.client.post("/api/v1/attempts",json={"events":[event]},headers=headers)
            self.assertEqual(response.status_code,200,response.data)
        dashboard=self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("Short Code Child",dashboard)
        self.assertIn("1 / 26",dashboard)
        other=self.app.test_client()
        self.post_form("/register",{"username":"second_short_parent","password":"strong-passphrase-456"},other)
        self.post_form("/login",{"username":"second_short_parent","password":"strong-passphrase-456"},other)
        self.post_form("/pair",{"code":"abcde9_x"},other)
        self.assertIn("Short Code Child",other.get("/dashboard").get_data(as_text=True))

    def test_new_eight_character_code_is_accepted_and_shorter_code_rejected(self):
        event={"id":"new-short-code-123","student_id":"new-short-child",
               "student_name":"New Short Child","pairing_code":"ABCD2345",
               "mode":"learn","target":"A","observed":"A","confidence":.95,
               "result":"correct","timestamp":"2026-11-09T12:00:00Z"}
        headers={"Authorization":"Bearer "+self.token}
        response=self.client.post("/api/v1/attempts",json={"events":[event]},headers=headers)
        self.assertEqual(response.status_code,200)
        event["pairing_code"]="ABCD234"
        response=self.client.post("/api/v1/attempts",json={"events":[event]},headers=headers)
        self.assertEqual(response.status_code,400)


if __name__=="__main__":
    unittest.main()
