import sqlite3

import requests

from app import clock_consistency_check

BASE = "http://127.0.0.1:5173"
health = requests.get(BASE + "/healthz")
assert health.status_code == 200, health.text
clock = health.json()["checks"]["clock"]
assert clock["status"] == "ok"
assert clock["clock_source"] == "application_utc_and_sqlite_utc"
assert clock["drift_seconds"] <= clock["warning_threshold_seconds"]

diagnostics = requests.get(BASE + "/api/diagnostics")
assert diagnostics.status_code == 200
assert diagnostics.json()["checks"]["clock"]["message"] == "Clock sources are consistent"

conn = sqlite3.connect("data/print_recovery.sqlite3")
conn.row_factory = sqlite3.Row
warning = clock_consistency_check(
    conn,
    threshold_seconds=5.0,
    application_timestamp="2000-01-01T00:00:00+00:00",
)
conn.close()
assert warning["status"] == "warning"
assert warning["drift_seconds"] > 5.0
assert "event ordering" in warning["message"]
print({"status": "passed", "clock_status": clock["status"], "warning_status": warning["status"]})
