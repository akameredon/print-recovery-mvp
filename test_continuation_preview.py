import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (100, 200), "white").save(source)
with source.open("rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("preview.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("preview.png",),
).fetchone()[0]
counts_before = conn.execute(
    "SELECT (SELECT COUNT(*) FROM decisions WHERE job_id=?), (SELECT COUNT(*) FROM events WHERE job_id=?)",
    (job_id, job_id),
).fetchone()
conn.close()
preview = requests.get(
    BASE + f"/api/jobs/{job_id}/continuation-preview",
    params={"y_mm": 100, "overlap_mm": 10},
)
assert preview.status_code == 200, preview.text
body = preview.json()
assert body["operator_confirmation_required"] is True
assert [region["label"] for region in body["regions"]] == [
    "printed",
    "uncertain",
    "remaining",
]
assert body["regions"][0]["end_y_mm"] == 90.0
assert body["regions"][1]["start_y_mm"] == 90.0
assert body["regions"][1]["end_y_mm"] == 110.0
assert body["regions"][2]["start_y_mm"] == 110.0
image = requests.get(BASE + body["preview_url"])
assert image.status_code == 200
assert image.headers["Content-Type"].startswith("image/")
conn = sqlite3.connect("data/print_recovery.sqlite3")
counts_after = conn.execute(
    "SELECT (SELECT COUNT(*) FROM decisions WHERE job_id=?), (SELECT COUNT(*) FROM events WHERE job_id=?)",
    (job_id, job_id),
).fetchone()
conn.close()
assert counts_before == counts_after
invalid = requests.get(BASE + f"/api/jobs/{job_id}/continuation-preview?y_mm=-1")
assert invalid.status_code == 400
assert invalid.json()["error"] == "PREVIEW_FAILED"
print({"status": "passed", "regions": [r["label"] for r in body["regions"]], "read_only": True})
