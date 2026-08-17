import os

import requests

BASE = "http://127.0.0.1:5173"
client = requests.Session()
prefix = f"day67_{os.getpid()}"
password = "day67-adapter-password"

tech = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_tech",
        "display_name": "Day 67 Technician",
        "role": "technician",
        "password": password,
    },
)
assert tech.status_code == 201, tech.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
    ).status_code
    == 200
)

payload = {
    "name": prefix + " observer",
    "adapter_type": "generic_rip_observer",
    "connection_mode": "trace_file",
    "trace_or_endpoint": "/var/lib/print-recovery/rip-trace.jsonl",
    "settings": {"poll_interval_seconds": 5, "read_only": True},
    "status": "ready",
    "enabled": False,
}
created = client.post(BASE + "/api/adapter-configurations", json=payload)
assert created.status_code == 201, created.text
configuration_id = created.json()["configuration"]["id"]
assert created.json()["configuration"]["workspace_id"] == "ws-default"
assert created.json()["configuration"]["settings"]["read_only"] is True

listed = client.get(BASE + "/api/adapter-configurations")
assert listed.status_code == 200
assert any(item["id"] == configuration_id for item in listed.json()["configurations"])

secret = client.post(
    BASE + "/api/adapter-configurations",
    json=dict(payload, name=prefix + " secret", settings={"api_token": "do-not-store"}),
)
assert secret.status_code == 400
assert secret.json()["error"] == "SECRET_NOT_ALLOWED"

operator = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_operator",
        "display_name": "Day 67 Operator",
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
forbidden = client.patch(
    BASE + f"/api/adapter-configurations/{configuration_id}",
    json=dict(payload, name=prefix + " operator-change"),
)
assert forbidden.status_code == 403
assert forbidden.json()["error"] == "ROLE_FORBIDDEN"
assert client.get(BASE + "/api/adapter-configurations").status_code == 200

assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_tech", "password": password}
    ).status_code
    == 200
)
updated = client.patch(
    BASE + f"/api/adapter-configurations/{configuration_id}",
    json=dict(payload, status="draft", settings={"read_only": True, "max_lines": 1000}),
)
assert updated.status_code == 200
assert updated.json()["configuration"]["settings"]["max_lines"] == 1000
retired = client.delete(BASE + f"/api/adapter-configurations/{configuration_id}")
assert retired.status_code == 200
assert not any(
    item["id"] == configuration_id
    for item in client.get(BASE + "/api/adapter-configurations").json()["configurations"]
)

html = client.get(BASE + "/").text
assert "Adapter configuration" in html
assert "Save adapter configuration" in html
print(
    {
        "status": "passed",
        "technician_only": True,
        "operator_blocked": True,
        "secret_rejected": True,
        "workspace_scoped": True,
    }
)
