import os

import requests

BASE = "http://127.0.0.1:5173"
client = requests.Session()
prefix = f"day64_{os.getpid()}"
password = "day64-audit-password"

created = client.post(
    BASE + "/api/users",
    json={
        "username": prefix,
        "display_name": "Day 64 Auditor",
        "role": "technician",
        "password": password,
    },
)
assert created.status_code == 201, created.text
login = client.post(BASE + "/api/session", json={"username": prefix, "password": password})
assert login.status_code == 200, login.text

profile = {
    "name": prefix + " profile",
    "manufacturer": "Mimaki",
    "printer_model": "JV33-130",
    "rip_name": "RasterLink7",
    "rip_version": "7.x",
    "connection_mode": "hotfolder",
    "job_input_path": "/jobs/incoming",
    "job_output_or_hotfolder": "/jobs/hotfolder",
    "observable_signals": ["queue", "progress"],
    "recovery_mode": "assisted_only",
}
created_profile = client.post(BASE + "/api/printer-profiles", json=profile)
assert created_profile.status_code == 201, created_profile.text
profile_id = created_profile.json()["profile"]["id"]
updated = client.patch(
    BASE + f"/api/printer-profiles/{profile_id}", json=dict(profile, status="ready")
)
assert updated.status_code == 200
retired = client.delete(BASE + f"/api/printer-profiles/{profile_id}")
assert retired.status_code == 200

all_audit = client.get(BASE + "/api/audit-log?limit=100")
assert all_audit.status_code == 200, all_audit.text
items = all_audit.json()["items"]
actions = {item["action"] for item in items if item["actor_username"] == prefix}
assert {
    "LOGIN_SUCCESS",
    "PRINTER_PROFILE_CREATED",
    "PRINTER_PROFILE_UPDATED",
    "PRINTER_PROFILE_RETIRED",
}.issubset(actions)
assert all("password" not in item["details"] for item in items)
filtered = client.get(
    BASE + "/api/audit-log", params={"action": "PRINTER_PROFILE_UPDATED", "actor": prefix}
)
assert filtered.status_code == 200
assert all(item["action"] == "PRINTER_PROFILE_UPDATED" for item in filtered.json()["items"])

logout = client.delete(BASE + "/api/session")
assert logout.status_code == 200
failed_login = client.post(
    BASE + "/api/session", json={"username": prefix, "password": "wrong-password"}
)
assert failed_login.status_code == 401
unauthenticated = client.get(BASE + "/api/audit-log")
assert unauthenticated.status_code == 401
print({"status": "passed", "searchable": True, "login_events": True, "configuration_events": True})
