import time, json, requests

DEFAULT_DELAYS = [1, 2, 4, 8, 16]

def notify_with_backoff(evaluation_url: str, payload: dict, delays=DEFAULT_DELAYS):
    headers = {"Content-Type": "application/json"}
    for delay in [0] + list(delays):
        if delay:
            time.sleep(delay)
        try:
            r = requests.post(evaluation_url, data=json.dumps(payload), headers=headers, timeout=10)
            if 200 <= r.status_code < 300:
                return True
        except Exception:
            pass
    return False
