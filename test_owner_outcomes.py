import os

import requests

BASE = "http://127.0.0.1:5173"
client = requests.Session()
prefix = f"day68_{os.getpid()}"
password = "day68-owner-password"

owner = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_owner",
        "display_name": "Day 68 Owner",
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

metrics = client.get(BASE + "/api/outcomes")
assert metrics.status_code == 200, metrics.text
body = metrics.json()
assert body["workspace_id"] == "ws-default"
assert "estimated_material_saved_m2" in body["metrics"]
assert "estimated_waste_m2" in body["metrics"]
assert "not a physical material measurement" in body["measurement_boundary"]

invalid = client.get(BASE + "/api/outcomes?date_from=not-a-date")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_OUTCOME_QUERY"

operator = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_operator",
        "display_name": "Day 68 Operator",
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
forbidden = client.get(BASE + "/api/outcomes")
assert forbidden.status_code == 403
assert forbidden.json()["error"] == "ROLE_FORBIDDEN"

html = client.get(BASE + "/").text
assert "Owner outcomes dashboard" in html
assert "Owner permission is required" in html
print({"status": "passed", "owner_only": True, "metrics": True, "boundary_wording": True})
