import requests

BASE = "http://127.0.0.1:5173"

missing = requests.get(BASE + "/api/does-not-exist", headers={"X-Correlation-ID": "day6-404"})
assert missing.status_code == 404
missing_body = missing.json()
assert missing_body["error"] == "NOT_FOUND"
assert missing_body["status"] == 404
assert missing_body["correlation_id"] == "day6-404"

wrong_method = requests.get(
    BASE + "/api/jobs/not-a-real-job/checkpoint",
    headers={"X-Correlation-ID": "day6-405"},
)
assert wrong_method.status_code == 405
wrong_body = wrong_method.json()
assert wrong_body["error"] == "METHOD_NOT_ALLOWED"
assert wrong_body["correlation_id"] == "day6-405"

browser_error = requests.get(
    BASE + "/does-not-exist", headers={"Accept": "text/html", "X-Correlation-ID": "day6-browser"}
)
assert browser_error.status_code == 404
assert "Return to the dashboard" in browser_error.text
assert "day6-browser" in browser_error.text

internal = requests.get(
    BASE + "/api/diagnostics",
    headers={"Accept": "application/json", "X-Correlation-ID": "day6-internal"},
)
assert internal.status_code == 200
print(
    {
        "status": "passed",
        "json_404": missing_body["error"],
        "json_405": wrong_body["error"],
        "browser_404": browser_error.status_code,
    }
)
