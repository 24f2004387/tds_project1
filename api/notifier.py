# api/notifier.py
import time
import json
import traceback
from typing import Dict, Any
import requests
LOG_PATH = "/tmp/notify.log"

def _append_log(line: str):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # best effort; don't crash the notifier
        print("[notify] failed to write log", traceback.format_exc())

def notify_with_backoff(evaluation_url: str, payload: Dict[str, Any], max_attempts: int = 6):
    """
    POST payload to evaluation_url with exponential backoff.
    Writes human-readable logs to stdout (visible in HF runtime logs)
    and appends them to /tmp/notify.log so you can fetch via the debug endpoint.
    """
    delays = [1, 2, 4, 8, 16, 32][:max_attempts]
    last_exc = None
    for attempt, d in enumerate(delays, start=1):
        try:
            print(f"[notify] Attempt {attempt} -> POST {evaluation_url} payload keys: {list(payload.keys())}")
            _append_log(f"[notify] Attempt {attempt} -> POST {evaluation_url} payload: {json.dumps(payload)}")
            resp = requests.post(evaluation_url, json=payload, timeout=20)
            text_snip = (resp.text or "")[:2000]
            log_line = f"[notify] response status={resp.status_code} headers={dict(resp.headers)} body_snip={text_snip}"
            print(log_line)
            _append_log(log_line)
            if resp.status_code == 200:
                print("[notify] Success")
                _append_log("[notify] Success")
                return True
            else:
                print(f"[notify] Non-200 status, will retry in {d}s")
                _append_log(f"[notify] Non-200 status {resp.status_code}, will retry in {d}s")
        except Exception as e:
            tb = traceback.format_exc()
            print("[notify] Exception when POSTing:", tb)
            _append_log("[notify] Exception when POSTing: " + tb)
            last_exc = e
        time.sleep(d)
    print("[notify] All attempts failed")
    _append_log("[notify] All attempts failed: " + (str(last_exc) if last_exc else "none"))
    return False
