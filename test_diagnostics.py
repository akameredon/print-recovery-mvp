import requests

BASE = "http://127.0.0.1:5173"
health = requests.get(BASE + "/healthz", headers={"X-Correlation-ID": "day5-health-test"})
assert health.status_code == 200, health.text
health_body = health.json()
assert health_body["status"] == "ok"
assert health_body["checks"]["database"]["schema_versions"] == [1, 2, 3, 4, 5]
assert health_body["checks"]["paths"]["status"] == "ok"
assert "request_correlation_id" not in health_body
assert health.headers.get("X-Correlation-ID") == "day5-health-test"

diagnostics = requests.get(
    BASE + "/api/diagnostics", headers={"X-Correlation-ID": "day5-diagnostics-test"}
)
assert diagnostics.status_code == 200, diagnostics.text
diagnostics_body = diagnostics.json()
assert diagnostics_body["status"] == "ok"
assert diagnostics_body["request_correlation_id"] == "day5-diagnostics-test"
assert "source_path" not in diagnostics_body["configuration"]
print(
    {
        "status": "passed",
        "health": health_body["status"],
        "schema_versions": health_body["checks"]["database"]["schema_versions"],
    }
)
