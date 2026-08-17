import io
import os

import requests

BASE = "http://127.0.0.1:5173"
client = requests.Session()
prefix = f"day65_{os.getpid()}"
password = "day65-workspace-password"

owner = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_owner",
        "display_name": "Day 65 Owner",
        "role": "owner",
        "password": password,
    },
)
assert owner.status_code == 201, owner.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)

workspace = client.post(BASE + "/api/workspaces", json={"name": prefix + " shop"})
assert workspace.status_code == 201, workspace.text
workspace_id = workspace.json()["workspace"]["id"]

technician = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_tech",
        "display_name": "Day 65 Technician",
        "role": "technician",
        "password": password,
        "workspace_id": workspace_id,
    },
)
assert technician.status_code == 201, technician.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
    ).status_code
    == 200
)

upload = client.post(
    BASE + "/api/jobs",
    files={"file": ("workspace-sample.png", io.BytesIO(b"synthetic workspace job"), "image/png")},
    data={"printer_model": "Mimaki", "rip_name": "RasterLink7"},
    allow_redirects=False,
)
assert upload.status_code == 302, upload.text
job_id = client.get(BASE + "/api/jobs").json()["jobs"][0]["id"]
job_detail = client.get(BASE + f"/api/jobs/{job_id}")
assert job_detail.status_code == 200
assert job_detail.json()["job"]["workspace_id"] == workspace_id
assert any(job["id"] == job_id for job in client.get(BASE + "/api/jobs").json()["jobs"])

assert client.delete(BASE + "/api/session").status_code == 200
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)
assert client.get(BASE + f"/api/jobs/{job_id}").status_code == 404
assert all(job["id"] != job_id for job in client.get(BASE + "/api/jobs").json()["jobs"])

assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
    ).status_code
    == 200
)
assert client.get(BASE + f"/api/jobs/{job_id}").status_code == 200
workspaces = client.get(BASE + "/api/workspaces").json()["workspaces"]
assert any(item["id"] == workspace_id for item in workspaces)
print(
    {
        "status": "passed",
        "job_isolation": True,
        "workspace_assignment": True,
        "cross_shop_blocked": True,
    }
)
