import io
import os

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"day69_{os.getpid()}"
password = "day69-conflict-password"
setup = requests.Session()
created = setup.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_owner",
        "display_name": "Day 69 Owner",
        "role": "owner",
        "password": password,
    },
)
assert created.status_code == 201, created.text
assert (
    setup.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)

upload = setup.post(
    BASE + "/api/jobs",
    files={"file": ("conflict-sample.png", io.BytesIO(b"synthetic conflict job"), "image/png")},
    data={
        "printer_model": "Mimaki",
        "rip_name": "RasterLink7",
        "media_width_mm": "1000",
        "media_length_mm": "2000",
    },
    allow_redirects=False,
)
assert upload.status_code == 302
job_id = setup.get(BASE + "/api/jobs").json()["jobs"][0]["id"]
job = setup.get(BASE + f"/api/jobs/{job_id}").json()["job"]
assert job["revision"] == 0

first_client = requests.Session()
second_client = requests.Session()
for client in (first_client, second_client):
    assert (
        client.post(
            BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
        ).status_code
        == 200
    )

first = first_client.post(
    BASE + f"/api/jobs/{job_id}/overlap", json={"overlap_mm": 12, "expected_revision": 0}
)
assert first.status_code == 200, first.text
assert first.json()["revision"] == 1

stale = second_client.post(
    BASE + f"/api/jobs/{job_id}/overlap", json={"overlap_mm": 20, "expected_revision": 0}
)
assert stale.status_code == 409, stale.text
assert stale.json()["error"] == "JOB_CONFLICT"
assert stale.json()["current_revision"] == 1

reloaded = second_client.get(BASE + f"/api/jobs/{job_id}").json()["job"]
retry = second_client.post(
    BASE + f"/api/jobs/{job_id}/overlap",
    json={"overlap_mm": 20, "expected_revision": reloaded["revision"]},
)
assert retry.status_code == 200, retry.text
assert retry.json()["revision"] == 2

invalid = first_client.post(
    BASE + f"/api/jobs/{job_id}/overlap", json={"overlap_mm": 25, "expected_revision": "bad"}
)
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_JOB_REVISION"
print({"status": "passed", "stale_action_blocked": True, "revision_reload": True, "retry": True})
