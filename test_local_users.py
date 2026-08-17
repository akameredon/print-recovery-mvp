import os

import requests

BASE = "http://127.0.0.1:5173"
PREFIX = f"day61_{os.getpid()}"
client = requests.Session()

for role in ("operator", "technician", "owner"):
    response = client.post(
        BASE + "/api/users",
        json={
            "username": f"{PREFIX}_{role}",
            "display_name": f"Day 61 {role.title()}",
            "role": role,
            "password": "day61-password-123",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["role"] == role
    assert body["user"]["active"] == 1

assert (
    client.post(
        BASE + "/api/session",
        json={"username": f"{PREFIX}_owner", "password": "day61-password-123"},
    ).status_code
    == 200
)
users = client.get(BASE + "/api/users")
assert users.status_code == 200
assert {user["role"] for user in users.json()["users"]} >= {"operator", "technician", "owner"}

operator = next(user for user in users.json()["users"] if user["username"] == f"{PREFIX}_operator")
selected = client.post(
    BASE + "/api/session", json={"username": operator["username"], "password": "day61-password-123"}
)
assert selected.status_code == 200
assert selected.json()["user"]["role"] == "operator"

current = client.get(BASE + "/api/session")
assert current.status_code == 200
assert current.json()["authenticated"] is True
assert current.json()["user"]["id"] == operator["id"]

assert (
    client.post(
        BASE + "/api/session",
        json={"username": operator["username"], "password": "day61-password-123"},
    ).status_code
    == 200
)

duplicate = client.post(
    BASE + "/api/users",
    json={
        "username": f"{PREFIX}_operator",
        "display_name": "Duplicate",
        "role": "owner",
        "password": "day61-password-123",
    },
)
assert duplicate.status_code == 409
assert duplicate.json()["error"] == "USER_EXISTS"

invalid = client.post(
    BASE + "/api/users",
    json={"username": "bad-role", "display_name": "Bad", "role": "administrator"},
)
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_USER"

html = client.get(BASE + "/").text
assert "Local user account" in html
assert "Create local account" in html
assert "Sessions expire after the configured inactivity window" in html
print({"status": "passed", "roles": ["operator", "technician", "owner"], "session": True})
