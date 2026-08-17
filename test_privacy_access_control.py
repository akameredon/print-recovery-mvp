import os

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"day70_{os.getpid()}"
password = "day70-privacy-password"
unauth = requests.Session()

for path in ("/api/users", "/api/workspaces", "/api/audit-log"):
    response = unauth.get(BASE + path)
    assert response.status_code == 401, (path, response.text)

owner = unauth.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_owner",
        "display_name": "Day 70 Owner",
        "role": "owner",
        "password": password,
    },
)
assert owner.status_code == 201, owner.text
assert (
    unauth.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)

users = unauth.get(BASE + "/api/users")
assert users.status_code == 200
assert all(user["workspace_id"] == "ws-default" for user in users.json()["users"])
workspaces = unauth.get(BASE + "/api/workspaces")
assert workspaces.status_code == 200
assert all(workspace["id"] == "ws-default" for workspace in workspaces.json()["workspaces"])

workspace = unauth.post(BASE + "/api/workspaces", json={"name": prefix + " private shop"})
assert workspace.status_code == 201
other_workspace_id = workspace.json()["workspace"]["id"]

operator = unauth.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_operator",
        "display_name": "Day 70 Operator",
        "role": "operator",
        "password": password,
    },
)
assert operator.status_code == 201, operator.text
assert (
    unauth.post(
        BASE + "/api/session", json={"username": prefix + "_operator", "password": password}
    ).status_code
    == 200
)
forbidden = unauth.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_blocked",
        "display_name": "Blocked",
        "role": "operator",
        "password": password,
        "workspace_id": other_workspace_id,
    },
)
assert forbidden.status_code == 403
assert forbidden.json()["error"] == "ROLE_FORBIDDEN"

html = unauth.get(BASE + "/").text
assert "Owner permission is required" in html or "Local user account" in html
print(
    {
        "status": "passed",
        "unauthenticated_listings_blocked": True,
        "workspace_scoped": True,
        "operator_account_creation_blocked": True,
    }
)
