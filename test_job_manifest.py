import hashlib
import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

from job_manifest import build_job_manifest

sample = {
    "id": "demo",
    "file_name": "sample.png",
    "source_path": "/tmp/sample.png",
    "source_hash": "expected",
    "printer_model": "Mimaki JV150-series",
    "rip_name": "RasterLink6",
    "orientation": "top-left",
    "media_width_mm": 100,
    "media_length_mm": 200,
    "origin_x_mm": 0,
    "origin_y_mm": 0,
    "overlap_mm": 5,
    "scale": 1,
    "resolution": "720x720",
    "passes": 4,
    "profile": "test",
}
assert (
    build_job_manifest(sample, source_exists=False, actual_hash=None, captured_at="now")["job"][
        "source_integrity"
    ]
    == "missing"
)
assert (
    build_job_manifest(sample, source_exists=True, actual_hash="other", captured_at="now")["job"][
        "source_integrity"
    ]
    == "changed"
)

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (80, 160), "white").save(source)
with source.open("rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("manifest.png", image_file, "image/png")},
        data={
            "printer_model": "Mimaki JV150-series",
            "rip_name": "RasterLink6",
            "media_width_mm": "100",
            "media_length_mm": "200",
        },
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id, source_path, source_hash = conn.execute(
    "SELECT id,source_path,source_hash FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("manifest.png",),
).fetchone()
conn.close()
manifest = requests.get(BASE + f"/api/jobs/{job_id}/manifest")
assert manifest.status_code == 200, manifest.text
body = manifest.json()
assert body["manifest_schema"] == "print-recovery.job-manifest/v1"
assert body["job"]["source_integrity"] == "verified"
assert body["job"]["source_hash"] == source_hash
assert (
    body["job"]["actual_source_hash"] == hashlib.sha256(Path(source_path).read_bytes()).hexdigest()
)
assert body["printer"]["model"] == "Mimaki JV150-series"
markdown = requests.get(BASE + f"/api/jobs/{job_id}/manifest?format=md")
assert markdown.status_code == 200
assert "# Job Manifest" in markdown.text
assert "host-side job evidence" in markdown.text
invalid = requests.get(BASE + f"/api/jobs/{job_id}/manifest?format=xml")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_MANIFEST_FORMAT"
print({"status": "passed", "json": True, "markdown": True, "hash_verified": True})
