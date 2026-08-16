import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (30, 30), "white").save(source)
with source.open("rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("confidence-badges.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "300"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("confidence-badges.png",),
).fetchone()[0]
conn.close()
for evidence in ("prepared", "transmitted", "acknowledged", "physical"):
    assert (
        requests.post(
            BASE + f"/api/jobs/{job_id}/checkpoint",
            json={"y_mm": 50, "band_mm": 5, "evidence": evidence},
        ).status_code
        == 200
    )
html = requests.get(BASE + "/?q=confidence-badges.png")
assert html.status_code == 200
for label in ("Prepared", "Transmitted", "Acknowledged", "Physically confirmed"):
    assert f">{label}</span>" in html.text
assert "confidence-badge" in html.text
assert "function confidenceBadges(id)" in html.text
job = requests.get(BASE + f"/api/jobs/{job_id}")
assert job.status_code == 200
assert {point["confidence"] for point in job.json()["checkpoints"]} == {
    "prepared",
    "transmitted",
    "acknowledged",
    "physically_confirmed",
}
print({"status": "passed", "job_id": job_id, "confidence_levels": 4})
