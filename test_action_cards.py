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
        files={"file": ("action-cards.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("action-cards.png",),
).fetchone()[0]
conn.close()
recommendation = requests.get(BASE + f"/api/jobs/{job_id}/recommendation")
assert recommendation.status_code == 200
assert recommendation.json()["recommendation"] in {"CONTINUE", "TEST_FIRST", "RESTART"}
html = requests.get(BASE + "/?q=action-cards.png")
assert html.status_code == 200
for label in ("Continue", "Test first", "Restart", "Recovery actions"):
    assert label in html.text
assert 'data-action="CONTINUE"' in html.text
assert 'data-action="TEST_FIRST"' in html.text
assert 'data-action="RESTART"' in html.text
assert "body.recommendation" in html.text
assert "classList.toggle('recommended'" in html.text
print({"status": "passed", "recommendation": recommendation.json()["recommendation"], "cards": 3})
