import os
from datetime import date, timedelta

import requests

BASE = "http://127.0.0.1:5173"
password = "day100-release-password"
username = f"day100_owner_{os.getpid()}"
client = requests.Session()
created = client.post(
    BASE + "/api/users",
    json={
        "username": username,
        "display_name": "Release Owner",
        "role": "owner",
        "password": password,
    },
)
assert created.status_code == 201, created.text
assert (
    client.post(
        BASE + "/api/session", json={"username": username, "password": password}
    ).status_code
    == 200
)
end = date.today()
start = end - timedelta(days=6)
window = {"pilot_start": start.isoformat(), "pilot_end": end.isoformat()}
insufficient = client.post(
    BASE + "/api/release-decision",
    json={
        **window,
        "decision": "release",
        "rationale": "Review complete",
        "evidence": {
            "field_validation_status": "software_recorded_only",
            "physical_test_count": 0,
            "support_review_complete": False,
        },
    },
)
assert insufficient.status_code == 409
assert insufficient.json()["error"] == "RELEASE_EVIDENCE_INSUFFICIENT"
extended = client.post(
    BASE + "/api/release-decision",
    json={
        **window,
        "decision": "extend_pilot",
        "rationale": "Need target-device field evidence",
        "evidence": {
            "field_validation_status": "software_recorded_only",
            "physical_test_count": 0,
            "support_review_complete": False,
        },
    },
)
assert extended.status_code == 201, extended.text
assert extended.json()["decision"]["decision"] == "extend_pilot"
latest = client.get(BASE + "/api/release-decision")
assert latest.status_code == 200
assert latest.json()["decision"]["decision"] == "extend_pilot"
print({"status": "passed", "release_gate": True, "extend_pilot": True, "audit_retrieval": True})
