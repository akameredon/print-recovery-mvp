import io
import os
import sqlite3
from datetime import datetime, timedelta, timezone

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"day73_{os.getpid()}"
password = "day73-success-password"
client = requests.Session()
bootstrap = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_bootstrap",
        "display_name": "Day 73 Bootstrap",
        "role": "owner",
        "password": password,
    },
)
assert bootstrap.status_code == 201, bootstrap.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_bootstrap", "password": password}
    ).status_code
    == 200
)
workspace_response = client.post(BASE + "/api/workspaces", json={"name": prefix + " shop"})
assert workspace_response.status_code == 201, workspace_response.text
workspace_id = workspace_response.json()["workspace"]["id"]

created = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_owner",
        "display_name": "Day 73 Owner",
        "role": "owner",
        "password": password,
        "workspace_id": workspace_id,
    },
)
assert created.status_code == 201, created.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)

upload = client.post(
    BASE + "/api/jobs",
    files={"file": ("success-rate.png", io.BytesIO(b"success rate job"), "image/png")},
    data={
        "printer_model": "Roland VG3",
        "rip_name": "VersaWorks",
        "media_width_mm": "1000",
        "media_length_mm": "2000",
    },
    allow_redirects=False,
)
assert upload.status_code == 302
job = next(
    item
    for item in client.get(BASE + "/api/jobs?q=success-rate.png").json()["jobs"]
    if item["file_name"] == "success-rate.png"
)
week_start = datetime.now(timezone.utc).date() - timedelta(
    days=datetime.now(timezone.utc).weekday()
)
created_at = datetime.now(timezone.utc).isoformat()
conn = sqlite3.connect("data/print_recovery.sqlite3")
for action, recommendation in (
    ("approved: aligned", "CONTINUE"),
    ("rejected: seam failed", "TEST_FIRST"),
    ("restart", "RESTART"),
    ("generated_continuation", "CONTINUE"),
):
    conn.execute(
        "INSERT INTO decisions(job_id,selected_y_mm,overlap_mm,mode,recommendation,confidence,operator_action,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (job["id"], 500.0, 5.0, "assisted", recommendation, "medium", action, created_at),
    )
conn.commit()
conn.close()

report = client.get(
    BASE + "/api/reports/recovery-success-rate?week_start=" + week_start.isoformat()
)
assert report.status_code == 200, report.text
body = report.json()
assert body["week_end"] == (week_start + timedelta(days=6)).isoformat()
assert body["categories"]["approved"] >= 1
assert body["categories"]["rejected"] >= 1
assert body["categories"]["restart"] >= 1
assert body["categories"]["pending"] >= 1
assert body["metrics"]["success_rate_percent"] == 50.0
assert "approved plus rejected" in body["success_rate_definition"]
assert "does not prove physical print quality" in body["measurement_boundary"]

invalid = client.get(BASE + "/api/reports/recovery-success-rate?week_start=bad-date")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_SUCCESS_RATE_QUERY"

operator = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_operator",
        "display_name": "Day 73 Operator",
        "role": "operator",
        "password": password,
        "workspace_id": workspace_id,
    },
)
assert operator.status_code == 201
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_operator", "password": password}
    ).status_code
    == 200
)
forbidden = client.get(
    BASE + "/api/reports/recovery-success-rate?week_start=" + week_start.isoformat()
)
assert forbidden.status_code == 403
assert forbidden.json()["error"] == "ROLE_FORBIDDEN"

assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)
html = client.get(BASE + "/").text
assert "Recovery success-rate report" in html
assert "Load success report" in html
print({"status": "passed", "categories_visible": True, "success_rate": 50.0, "owner_only": True})
