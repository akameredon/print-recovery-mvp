import hashlib
import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

from recovery_safety import assess_recovery_safety

blocked_missing = assess_recovery_safety(
    source_integrity="missing", has_checkpoint=True, has_interruption=True
)
assert blocked_missing["safe_to_generate"] is False
assert blocked_missing["blockers"][0]["code"] == "SOURCE_MISSING"
blocked_checkpoint = assess_recovery_safety(
    source_integrity="verified", has_checkpoint=False, has_interruption=True
)
assert blocked_checkpoint["status"] == "blocked"
assert blocked_checkpoint["blockers"][0]["code"] == "CHECKPOINT_MISSING"
ready = assess_recovery_safety(
    source_integrity="verified", has_checkpoint=True, has_interruption=True
)
assert ready["safe_to_generate"] is True

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = Path(handle.name)
Image.new("RGB", (60, 120), "white").save(source)
with source.open("rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("safety.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id, source_path, source_hash = conn.execute(
    "SELECT id,source_path,source_hash FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("safety.png",),
).fetchone()
conn.close()
no_checkpoint = requests.post(BASE + f"/api/jobs/{job_id}/continuation", json={"y_mm": 50})
assert no_checkpoint.status_code == 409
assert no_checkpoint.json()["error"] == "RECOVERY_BLOCKED"
assert "CHECKPOINT_MISSING" in {
    blocker["code"] for blocker in no_checkpoint.json()["recovery_safety"]["blockers"]
}
with open(source_path, "ab") as changed:
    changed.write(b"changed")
assert hashlib.sha256(Path(source_path).read_bytes()).hexdigest() != source_hash
conn = sqlite3.connect("data/print_recovery.sqlite3")
conn.execute(
    "INSERT INTO checkpoints(job_id,y_mm,band_mm,state,evidence,confidence,created_at) VALUES(?,?,?,?,?,?,datetime('now'))",
    (job_id, 50, 1, "PRINTING", "transmitted", "transmitted"),
)
conn.commit()
conn.close()
changed_source = requests.post(BASE + f"/api/jobs/{job_id}/continuation", json={"y_mm": 50})
assert changed_source.status_code == 409
assert changed_source.json()["error"] == "RECOVERY_BLOCKED"
assert "SOURCE_CHANGED" in {
    blocker["code"] for blocker in changed_source.json()["recovery_safety"]["blockers"]
}
print({"status": "passed", "missing_blocked": True, "changed_blocked": True})
