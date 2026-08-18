import os
import sqlite3
import stat

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"day82_{os.getpid()}"
password = "day82-secrets-password"
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
assert owner.status_code == 201, owner.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)
payload = {
    "name": "Encrypted adapter",
    "adapter_type": "generic_rip_observer",
    "connection_mode": "trace_file",
    "trace_or_endpoint": "trace.jsonl",
    "settings": {"poll_seconds": 5},
    "secrets": {"api_token": "do-not-return-this", "password": "also-secret"},
}
created = client.post(BASE + "/api/adapter-configurations", json=payload)
assert created.status_code == 201, created.text
configuration = created.json()["configuration"]
assert configuration["secret_storage"] == {"encrypted": True, "plaintext_returned": False}
assert "api_token" not in configuration["settings"]
assert "do-not-return-this" not in created.text
assert "password" not in created.text.lower()
conn = sqlite3.connect("data/print_recovery.sqlite3")
row = conn.execute(
    "SELECT settings,secret_ciphertext FROM adapter_configurations WHERE id=?",
    (configuration["id"],),
).fetchone()
conn.close()
assert "do-not-return-this" not in row[0]
assert "do-not-return-this" not in row[1]
assert row[1]
key_path = "data/.local-secrets.key"
mode = stat.S_IMODE(os.stat(key_path).st_mode)
assert mode == 0o600, oct(mode)
legacy_rejected = client.post(
    BASE + "/api/adapter-configurations",
    json={**payload, "name": "Legacy secret", "settings": {"password": "plaintext"}, "secrets": {}},
)
assert legacy_rejected.status_code == 400
assert legacy_rejected.json()["error"] == "SECRET_NOT_ALLOWED"
print(
    {
        "status": "passed",
        "encrypted": True,
        "plaintext_excluded": True,
        "key_mode": oct(mode),
        "legacy_rejection": True,
    }
)
