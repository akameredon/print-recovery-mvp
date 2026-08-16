import sqlite3
import tempfile

import requests
from PIL import Image

from checkpoint_confidence import calculate_checkpoint_confidence

assert calculate_checkpoint_confidence(
    {"evidence": "physical", "y_mm": 100, "logical_band": 3, "pass_number": 2}
) == {
    "score": 1.0,
    "level": "high",
    "factors": [
        "evidence:physical",
        "logical_band_and_pass_present:+0.05",
        "non_negative_coordinate:+0.00",
    ],
}
medium = calculate_checkpoint_confidence(
    {"evidence": "acknowledged", "y_mm": 100, "logical_band": None, "pass_number": None}
)
assert medium["score"] == 0.75
assert medium["level"] == "medium"
low = calculate_checkpoint_confidence({"evidence": "prepared", "y_mm": -1})
assert low["score"] == 0.0
assert low["level"] == "low"

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = handle.name
Image.new("RGB", (20, 20), "white").save(source)
with open(source, "rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("confidence.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("confidence.png",),
).fetchone()[0]
conn.close()
checkpoint = requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint",
    json={
        "y_mm": 100,
        "evidence": "acknowledged",
        "logical_band": 2,
        "pass_number": 1,
    },
)
assert checkpoint.status_code == 200, checkpoint.text
assert checkpoint.json()["confidence_rules"]["level"] == "medium"
readiness = requests.get(BASE + f"/api/jobs/{job_id}/readiness")
assert readiness.status_code == 200, readiness.text
assert readiness.json()["checkpoint_confidence"]["score"] == 0.8
print({"status": "passed", "pure_rules": True, "api_exposed": True})
