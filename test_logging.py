import json
from pathlib import Path

import requests

BASE = "http://127.0.0.1:5173"
response = requests.get(BASE + "/", headers={"X-Correlation-ID": "day2-test-correlation"})
assert response.status_code == 200
assert response.headers.get("X-Correlation-ID") == "day2-test-correlation"

log_path = Path(__file__).resolve().parent / "data" / "print_recovery.log"
lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
assert lines, "Expected structured log lines"
records = [json.loads(line) for line in lines[-20:]]
record = next(item for item in reversed(records) if item.get("route") == "/")
assert record["severity"] in {"INFO", "WARNING", "ERROR", "DEBUG"}
assert record["module"] == "print_recovery"
assert record["correlation_id"] == "day2-test-correlation"
assert "timestamp" in record
print(
    {
        "status": "passed",
        "correlation_id": record["correlation_id"],
        "log_records_checked": len(records),
    }
)
