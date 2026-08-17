import os

import requests

BASE = "http://127.0.0.1:5173"
client = requests.Session()
prefix = f"day66_{os.getpid()}"
password = "day63-technician-password"
account = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_tech",
        "display_name": "Day 63 Technician",
        "role": "technician",
        "password": password,
    },
)
assert account.status_code == 201, account.text
login = client.post(
    BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
)
assert login.status_code == 200, login.text
base = {
    "name": prefix,
    "manufacturer": "Mimaki",
    "printer_model": "JV33-130",
    "rip_name": "RasterLink7",
    "rip_version": "7.x",
    "connection_mode": "hotfolder",
    "job_input_path": "/jobs/incoming",
    "job_output_or_hotfolder": "/jobs/hotfolder",
    "observable_signals": ["queue", "progress", "completion"],
    "recovery_mode": "assisted_only",
    "status": "ready",
}

created = client.post(BASE + "/api/printer-profiles", json=base)
assert created.status_code == 201, created.text
profile = created.json()["profile"]
assert profile["manufacturer"] == "Mimaki"
assert profile["observable_signals"] == ["queue", "progress", "completion"]
assert profile["physical_validation_required"] is True

second = dict(
    base,
    name=prefix + "-roland",
    manufacturer="Roland",
    printer_model="VG3-540",
    rip_name="VersaWorks",
)
assert client.post(BASE + "/api/printer-profiles", json=second).status_code == 201
listed = client.get(BASE + "/api/printer-profiles")
assert listed.status_code == 200
assert listed.json()["count"] >= 2

duplicate = client.post(BASE + "/api/printer-profiles", json=base)
assert duplicate.status_code == 409
assert duplicate.json()["error"] == "PROFILE_EXISTS"

operator_account = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_operator",
        "display_name": "Day 63 Operator",
        "role": "operator",
        "password": password,
    },
)
assert operator_account.status_code == 201, operator_account.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_operator", "password": password}
    ).status_code
    == 200
)
forbidden = client.patch(
    BASE + f"/api/printer-profiles/{profile['id']}",
    json=dict(base, name=prefix + "-operator-change"),
)
assert forbidden.status_code == 403
assert forbidden.json()["error"] == "ROLE_FORBIDDEN"
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
    ).status_code
    == 200
)

unsafe = client.post(
    BASE + "/api/printer-profiles",
    json=dict(base, name=prefix + "-unsafe", recovery_mode="automatic"),
)
assert unsafe.status_code == 400
assert unsafe.json()["error"] == "UNSAFE_RECOVERY_MODE"

updated = dict(base, name=prefix + "-updated", status="draft", observable_signals=["host_progress"])
changed = client.patch(BASE + f"/api/printer-profiles/{profile['id']}", json=updated)
assert changed.status_code == 200
assert changed.json()["profile"]["name"] == prefix + "-updated"

retired = client.delete(BASE + f"/api/printer-profiles/{profile['id']}")
assert retired.status_code == 200
assert client.get(BASE + f"/api/printer-profiles/{profile['id']}").status_code == 404

html = client.get(BASE + "/").text
assert "Printer profiles" in html
assert "Save printer profile" in html
print(
    {
        "status": "passed",
        "multiple_profiles": True,
        "safety_validation": True,
        "operator_blocked": True,
        "retirement": True,
    }
)
