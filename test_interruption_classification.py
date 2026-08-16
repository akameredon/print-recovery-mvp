import sqlite3
import tempfile

import requests
from PIL import Image

from interruption_classification import classify_interruption

expected = {
    "POWER_LOSS": "outage",
    "PROTECTION_TRIP": "outage",
    "PRINTER_ERROR": "crash",
    "OPERATOR_ABORT": "abort",
    "COMMUNICATION_LOSS": "communication_loss",
    "MATERIAL_ISSUE": "material_issue",
    "UNKNOWN": "unknown",
}
for reason, classification in expected.items():
    result = classify_interruption(reason, "operator observed stop", "test")
    assert result["reason"] == reason
    assert result["classification"] == classification
    assert "operator note present" in result["evidence_requirements"]
assert classify_interruption("not-a-reason")["reason"] == "UNKNOWN"

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = handle.name
Image.new("RGB", (20, 20), "white").save(source)
with open(source, "rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("classification.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("classification.png",),
).fetchone()[0]
conn.close()
interruption = requests.post(
    BASE + f"/api/jobs/{job_id}/interrupt",
    json={"reason": "PROTECTION_TRIP", "note": "Thunder protector tripped"},
)
assert interruption.status_code == 200, interruption.text
body = interruption.json()
assert body["classification"]["classification"] == "outage"
conn = sqlite3.connect("data/print_recovery.sqlite3")
payload = conn.execute(
    "SELECT payload FROM events WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
).fetchone()[0]
conn.close()
assert '"classification"' in payload
print({"status": "passed", "matrix_rows": len(expected), "api_persistence": True})
