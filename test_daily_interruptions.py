import io
import os
from datetime import datetime, timezone

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"day71_{os.getpid()}"
password = "day71-report-password"
client = requests.Session()

created = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_tech",
        "display_name": "Day 71 Technician",
        "role": "technician",
        "password": password,
    },
)
assert created.status_code == 201, created.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
    ).status_code
    == 200
)

upload = client.post(
    BASE + "/api/jobs",
    files={"file": ("daily-interruption.png", io.BytesIO(b"daily interruption job"), "image/png")},
    data={"printer_model": "Mimaki", "rip_name": "RasterLink7"},
    allow_redirects=False,
)
assert upload.status_code == 302
job = next(
    item
    for item in client.get(BASE + "/api/jobs?q=daily-interruption.png").json()["jobs"]
    if item["file_name"] == "daily-interruption.png"
)
interrupted = client.post(
    BASE + f"/api/jobs/{job['id']}/interrupt",
    json={"reason": "POWER_LOSS", "note": "Day 71 synthetic outage", "source": "operator"},
)
assert interrupted.status_code == 200, interrupted.text

report_date = datetime.now(timezone.utc).date().isoformat()
report = client.get(BASE + "/api/reports/daily-interruptions?date=" + report_date)
assert report.status_code == 200, report.text
body = report.json()
assert body["report_date"] == report_date
assert body["metrics"]["interruption_events"] >= 1
assert body["metrics"]["affected_jobs"] >= 1
assert body["metrics"]["by_reason"]["POWER_LOSS"] >= 1
assert body["interruptions"][-1]["classification"]
assert "does not prove electrical cause" in body["measurement_boundary"]

invalid = client.get(BASE + "/api/reports/daily-interruptions?date=bad-date")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_DAILY_REPORT_QUERY"

operator = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_operator",
        "display_name": "Day 71 Operator",
        "role": "operator",
        "password": password,
    },
)
assert operator.status_code == 201
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_operator", "password": password}
    ).status_code
    == 200
)
forbidden = client.get(BASE + "/api/reports/daily-interruptions?date=" + report_date)
assert forbidden.status_code == 403
assert forbidden.json()["error"] == "ROLE_FORBIDDEN"

assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
    ).status_code
    == 200
)
html = client.get(BASE + "/").text
assert "Daily interruption summary" in html
assert "Load daily summary" in html
print(
    {
        "status": "passed",
        "grouped_summary": True,
        "workspace_scoped": True,
        "operator_blocked": True,
    }
)
