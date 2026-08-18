import os
from datetime import date, timedelta

import requests

BASE = "http://127.0.0.1:5173"
password = "day99-pilot-password"
username = f"day99_owner_{os.getpid()}"
client = requests.Session()
created = client.post(
    BASE + "/api/users",
    json={
        "username": username,
        "display_name": "Pilot Owner",
        "role": "owner",
        "password": password,
    },
)
assert created.status_code == 201, created.text
assert (
    client.post(
        BASE + "/api/session", json={"username": username, "password": password}
    ).status_code
    == 200
)
end = date.today()
start = end - timedelta(days=6)
window = {"pilot_start": start.isoformat(), "pilot_end": end.isoformat()}
invalid = client.get(
    BASE + "/api/pilot/report",
    params={"pilot_start": start.isoformat(), "pilot_end": (end - timedelta(days=1)).isoformat()},
)
assert invalid.status_code == 400
report = client.get(BASE + "/api/pilot/report", params=window)
assert report.status_code == 200, report.text
assert report.json()["pilot_status"] == "report_ready_for_support_review"
review = client.post(
    BASE + "/api/pilot/support-review",
    json={**window, "note": "Reviewed event log and backup status.", "issue_count": 1},
)
assert review.status_code == 201, review.text
report_after = client.get(BASE + "/api/pilot/report", params=window)
assert report_after.status_code == 200
assert report_after.json()["support_reviews"][0]["issue_count"] == 1
print({"status": "passed", "seven_day_window": True, "support_review": True, "report_ready": True})
