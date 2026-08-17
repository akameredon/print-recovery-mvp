import io
import os

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"days76_80_{os.getpid()}"
password = "days76-80-password"
client = requests.Session()
bootstrap = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_bootstrap",
        "display_name": "Bootstrap",
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
workspace = client.post(BASE + "/api/workspaces", json={"name": prefix + " shop"})
assert workspace.status_code == 201, workspace.text
workspace_id = workspace.json()["workspace"]["id"]
owner = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_owner",
        "display_name": "Owner",
        "role": "owner",
        "password": password,
        "workspace_id": workspace_id,
    },
)
tech = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_tech",
        "display_name": "Technician",
        "role": "technician",
        "password": password,
        "workspace_id": workspace_id,
    },
)
assert owner.status_code == 201 and tech.status_code == 201
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)
upload = client.post(
    BASE + "/api/jobs",
    files={"file": ("ops.png", io.BytesIO(b"ops"), "image/png")},
    data={"printer_model": "Mimaki", "rip_name": "RasterLink7"},
    allow_redirects=False,
)
assert upload.status_code == 302, upload.text
job = client.get(BASE + "/api/jobs?q=ops.png").json()["jobs"][0]
interrupted = client.post(
    BASE + f"/api/jobs/{job['id']}/interrupt",
    json={"reason": "POWER_LOSS", "note": "Utility outage"},
)
assert interrupted.status_code == 200, interrupted.text
assert interrupted.json()["notifications_created"] >= 1
notifications = client.get(BASE + "/api/notifications?unread=1")
assert notifications.status_code == 200 and notifications.json()["notifications"]
notification_id = notifications.json()["notifications"][0]["id"]
assert client.post(BASE + f"/api/notifications/{notification_id}/read").status_code == 200
email = client.put(
    BASE + "/api/settings/email-notifications",
    json={"email_enabled": True, "email_recipients": ["owner@example.com"]},
)
assert (
    email.status_code == 200
    and email.json()["delivery_status"] == "configuration_only_no_external_send"
)
assert client.get(BASE + "/api/settings/email-notifications").json()["settings"][
    "email_recipients"
] == ["owner@example.com"]
assert client.put(BASE + "/api/settings/retention", json={"retention_days": 30}).status_code == 200
assert client.get(BASE + "/api/settings/retention").json()["retention_days"] == 30
assert (
    client.post(
        BASE + "/api/backups/status", json={"status": "succeeded", "archive_name": "backup.zip"}
    ).status_code
    == 200
)
assert client.get(BASE + "/api/backups/status").json()["backups"][0]["status"] == "succeeded"
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
    ).status_code
    == 200
)
bundle = client.get(BASE + f"/api/jobs/{job['id']}/support-bundle")
assert bundle.status_code == 200, bundle.text
body = bundle.json()
assert body["bundle_type"] == "technician_support"
assert "password_hash" in body["excluded_secrets"]
assert "SMTP passwords" in body["excluded_secrets"]
assert "source_hash" in body["job"]
print(
    {
        "status": "passed",
        "notification": True,
        "email_safe": True,
        "retention": True,
        "backup_status": True,
        "support_bundle": True,
    }
)
