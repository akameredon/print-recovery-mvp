import os
import sqlite3

import requests

BASE = "http://127.0.0.1:5173"
prefix = f"day85_{os.getpid()}"
password = "day85-crash-password"
client = requests.Session()
created = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_owner",
        "display_name": "Crash Owner",
        "role": "owner",
        "password": password,
    },
)
assert created.status_code == 201, created.text
assert (
    client.post(
        BASE + "/api/session", json={"username": prefix + "_owner", "password": password}
    ).status_code
    == 200
)
conn = sqlite3.connect("data/print_recovery.sqlite3")
conn.execute(
    "INSERT INTO audit_log(action,resource_type,details,created_at) VALUES(?,?,?,datetime('now'))",
    (
        "TEST_CRASH",
        "diagnostics",
        '{"password":"should-not-export","source_path":"/home/ubuntu/private/source.png"}',
    ),
)
conn.commit()
conn.close()
report = client.get(BASE + "/api/diagnostics/crash-report")
assert report.status_code == 200, report.text
body = report.json()
assert body["report_type"] == "structured_crash_report"
assert body["redaction"]["secrets_removed"] is True
assert body["redaction"]["raw_log_export"] is False
assert "password" not in report.text.lower()
assert "/home/ubuntu/private" not in report.text
assert "print_recovery_crash_report.json" in report.headers.get("Content-Disposition", "")
operator = client.post(
    BASE + "/api/users",
    json={
        "username": prefix + "_operator",
        "display_name": "Operator",
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
forbidden = client.get(BASE + "/api/diagnostics/crash-report")
assert forbidden.status_code == 403
assert forbidden.json()["error"] == "ROLE_FORBIDDEN"
print({"status": "passed", "structured": True, "redacted": True, "owner_only": True})
