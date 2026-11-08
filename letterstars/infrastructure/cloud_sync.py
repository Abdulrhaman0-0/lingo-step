"""Offline-first HTTPS progress sync with an idempotent, durable outbox."""
import json
import os
import threading
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def allowed_cloud_url(url):
    if not url:
        return False
    target=urlsplit(url)
    return (target.scheme=="https" or
            (target.scheme=="http" and target.hostname in ("localhost","127.0.0.1"))) and bool(target.netloc)


class CloudSync:
    def __init__(self, store, url=None, token=None):
        self.store=store
        self.url=(url if url is not None else os.getenv("LINGOSTEP_CLOUD_URL","")).rstrip("/")
        self.token=token if token is not None else os.getenv("LINGOSTEP_DEVICE_TOKEN","")
        self.last_error=""
        self.enabled=bool(self.url and self.token and allowed_cloud_url(self.url))
        self._lock=threading.Lock()
        if self.url and not allowed_cloud_url(self.url):
            self.last_error="Cloud URL must use HTTPS (HTTP only on localhost)."

    def sync_once(self):
        if not self.enabled:
            return 0
        # Prevent concurrent network upload tasks from racing on the same events.
        if not self._lock.acquire(blocking=False):
            return 0
        try:
            events=self.store.pending_sync(50)
            if not events:
                return 0
            body=json.dumps({"events":events},ensure_ascii=False).encode("utf-8")
            req=Request(self.url+"/api/v1/attempts",data=body,
                headers={"Authorization":"Bearer "+self.token,
                         "Content-Type":"application/json"},
                method="POST")
            try:
                with urlopen(req,timeout=8) as response:
                    if response.status!=200:
                        raise RuntimeError("Unexpected server status")
                    accepted=json.loads(response.read(200_000)).get("accepted_ids",[])
                pending={item["id"] for item in events}
                if not isinstance(accepted,list) or any(x not in pending for x in accepted):
                    raise RuntimeError("Invalid cloud acknowledgement")
                self.store.mark_synced(accepted)
                self.last_error=""
                return len(accepted)
            except Exception as exc:
                self.last_error=f"{type(exc).__name__}: {exc}"
                return 0
        finally:
            self._lock.release()
