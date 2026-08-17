import requests

BASE = "http://127.0.0.1:5173"
health = requests.get(BASE + "/healthz")
assert health.status_code == 200, health.text
body = health.json()
assert body["status"] == "ok"
assert body["checks"]["database"]["integrity"]["status"] == "ok"
assert body["checks"]["database"]["integrity"]["quick_check"] == ["ok"]
assert body["checks"]["database"]["integrity"]["integrity_check"] == ["ok"]
assert body["checks"]["database"]["integrity"]["foreign_key_violations"] == []
endpoint = requests.get(BASE + "/api/diagnostics/database-integrity")
assert endpoint.status_code == 200, endpoint.text
endpoint_body = endpoint.json()
assert endpoint_body["status"] == "ok"
assert endpoint_body["message"] == "Database integrity checks passed"
diagnostics = requests.get(BASE + "/api/diagnostics").json()
assert diagnostics["checks"]["database"]["integrity"]["status"] == "ok"
print({"status": "passed", "quick_check": True, "foreign_keys": True, "diagnostics": True})
