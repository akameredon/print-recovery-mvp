import io
import os

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"day75_{os.getpid()}"
password = "day75-print-password"
client = requests.Session()
created = client.post(
    BASE + "/api/users",
    json={
        "username": prefix,
        "display_name": "Day 75 Owner",
        "role": "owner",
        "password": password,
    },
)
assert created.status_code == 201, created.text
assert (
    client.post(BASE + "/api/session", json={"username": prefix, "password": password}).status_code
    == 200
)
upload = client.post(
    BASE + "/api/jobs",
    files={"file": ("printable.png", io.BytesIO(b"printable report"), "image/png")},
    data={"printer_model": "Mimaki", "rip_name": "RasterLink7"},
    allow_redirects=False,
)
assert upload.status_code == 302, upload.text
job = client.get(BASE + "/api/jobs?q=printable.png").json()["jobs"][0]
report = client.get(BASE + f"/api/jobs/{job['id']}/recovery-report?format=print")
assert report.status_code == 200, report.text
assert report.headers["Content-Type"].startswith("text/html")
assert "window.print()" in report.text
assert "Safety boundary" in report.text
assert "physical printer position" in report.text
assert "recovery_report.html" in report.headers.get("Content-Disposition", "")
invalid = client.get(BASE + f"/api/jobs/{job['id']}/recovery-report?format=xml")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_REPORT_FORMAT"
assert "Print or save recovery report" in client.get(BASE + "/").text
print({"status": "passed", "print_html": True, "safety_boundary": True, "dashboard_link": True})
