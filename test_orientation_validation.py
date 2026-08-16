import sqlite3
import tempfile

import requests
from PIL import Image

from orientation_validation import validate_orientation_origin

verified = validate_orientation_origin(
    image_width_px=100,
    image_height_px=200,
    media_width_mm=100,
    media_length_mm=200,
    origin_x_mm=0,
    origin_y_mm=0,
    orientation="top-left",
)
assert verified["status"] == "verified"
assert verified["warnings"] == []
warning = validate_orientation_origin(
    image_width_px=300,
    image_height_px=200,
    media_width_mm=100,
    media_length_mm=200,
    origin_x_mm=120,
    origin_y_mm=0,
    orientation="bottom-right",
)
assert warning["status"] == "warning"
assert {item["code"] for item in warning["warnings"]} == {
    "ASPECT_RATIO_MISMATCH",
    "ORIGIN_OUTSIDE_MEDIA",
}
invalid = validate_orientation_origin(
    image_width_px=100,
    image_height_px=200,
    media_width_mm=100,
    media_length_mm=200,
    origin_x_mm=0,
    origin_y_mm=0,
    orientation="sideways",
)
assert invalid["status"] == "invalid"

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = handle.name
Image.new("RGB", (100, 200), "white").save(source)
with open(source, "rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("orientation.png", image_file, "image/png")},
        data={
            "media_width_mm": "100",
            "media_length_mm": "200",
            "orientation": "top-right",
        },
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("orientation.png",),
).fetchone()[0]
orientation = conn.execute("SELECT orientation FROM jobs WHERE id=?", (job_id,)).fetchone()[0]
conn.close()
assert orientation == "top-right"
api = requests.get(BASE + f"/api/jobs/{job_id}/orientation")
assert api.status_code == 200, api.text
assert api.json()["status"] == "verified"
assert api.json()["orientation"] == "top-right"
print({"status": "passed", "verified": True, "warning_matrix": True, "api": True})
