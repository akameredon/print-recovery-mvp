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
        files={"file": ("accessibility-controls.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("accessibility-controls.png",),
).fetchone()[0]
conn.close()
html = requests.get(BASE + "/?q=accessibility-controls.png")
assert html.status_code == 200
for marker in (
    'class="skip-link"',
    'href="#main-content"',
    'id="main-content"',
    ":focus-visible",
    'aria-live="polite"',
    f'data-job="{job_id}"',
):
    assert marker in html.text
assert "Show recovery recommendation" in html.text
assert "Review recovery decision" in html.text
print({"status": "passed", "keyboard_controls": True, "live_regions": True})
