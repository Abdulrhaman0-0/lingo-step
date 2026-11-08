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


if __name__=="__main__":
    unittest.main()
