import io
import os

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"day72_{os.getpid()}"
password = "day72-weekly-password"
client = requests.Session()

created = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_owner",
        "display_name": "Day 72 Owner",
        "role": "owner",
        "password": password,
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
    files={"file": ("weekly-waste.png", io.BytesIO(b"weekly waste job"), "image/png")},
    data={
        "printer_model": "Mimaki JV300",
        "rip_name": "RasterLink7",
        "media_width_mm": "1000",
        "media_length_mm": "2000",
    },
    allow_redirects=False,
)
assert upload.status_code == 302
job = next(
    item
    for item in client.get(BASE + "/api/jobs?q=weekly-waste.png").json()["jobs"]
    if item["file_name"] == "weekly-waste.png"
)

# The report is intentionally verified for a date range with no decisions as well as its schema.
report = client.get(BASE + "/api/reports/weekly-material-waste?week_start=2026-08-17")
assert report.status_code == 200, report.text
body = report.json()
assert body["week_start"] == "2026-08-17"
assert body["week_end"] == "2026-08-23"
assert body["metrics"]["jobs_created"] >= 1
assert "estimated_material_saved_m2" in body["metrics"]
assert "estimated_waste_m2" in body["metrics"]
assert "not a physical material measurement" in body["measurement_boundary"]

invalid = client.get(BASE + "/api/reports/weekly-material-waste?week_start=not-a-date")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_WEEKLY_REPORT_QUERY"

operator = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_operator",
        "display_name": "Day 72 Operator",
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
forbidden = client.get(BASE + "/api/reports/weekly-material-waste?week_start=2026-08-17")
assert forbidden.status_code == 403
assert forbidden.json()["error"] == "ROLE_FORBIDDEN"

assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)
html = client.get(BASE + "/").text
assert "Weekly material-waste report" in html
assert "Load weekly report" in html
print({"status": "passed", "weekly_range": True, "owner_only": True, "boundary_wording": True})
