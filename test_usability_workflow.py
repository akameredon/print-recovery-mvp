import requests

BASE = "http://127.0.0.1:5173"
html = requests.get(BASE + "/").text
assert "Operator paper workflow" in html
assert 'id="workflow-guide"' in html
assert 'aria-labelledby="workflow-title"' in html
assert "Print checklist" in html
assert "window.print()" in html
assert "@media print" in html
for step in ("Stabilize", "Identify", "Verify", "Choose", "Approve", "Validate"):
    assert f"<strong>{step}:</strong>" in html
assert "Tick each step on paper before proceeding." in html
print({"status": "passed", "workflow_steps": 6, "print_checklist": True})
