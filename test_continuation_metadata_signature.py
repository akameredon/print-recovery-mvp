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
    uploaded = requests.post(
        BASE + "/api/jobs",
        files={"file": ("signed-continuation.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert uploaded.status_code == 302, uploaded.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("signed-continuation.png",),
).fetchone()[0]
conn.execute(
    "INSERT INTO checkpoints(job_id,y_mm,band_mm,state,evidence,confidence,created_at) VALUES(?,?,?,?,?,?,datetime('now'))",
    (job_id, 100, 1, "captured", "transmitted", "medium"),
)
conn.execute(
    "INSERT INTO events(job_id,event_type,source,payload,created_at) VALUES(?,?,?,?,datetime('now'))",
    (job_id, "INTERRUPTED", "test", '{"classification":{"classification":"outage"}}'),
)
conn.commit()
conn.close()
continuation = requests.post(
    BASE + f"/api/jobs/{job_id}/continuation", json={"y_mm": 100, "overlap_mm": 5}
)
assert continuation.status_code == 200, continuation.text
body = continuation.json()
assert body["signed_metadata"]["job_id"] == job_id
assert body["metadata_signature"]
verified = requests.get(
    BASE + f"/api/jobs/{job_id}/continuation-metadata", params={"file": body["file"]}
)
assert verified.status_code == 200, verified.text
assert verified.json()["verified"] is True
assert verified.json()["verification_status"] == "verified"
conn = sqlite3.connect("data/print_recovery.sqlite3")
row = conn.execute(
    "SELECT id,payload FROM events WHERE job_id=? AND event_type='CONTINUATION_GENERATED' ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()
conn.execute(
    "UPDATE events SET payload=? WHERE id=?",
    (
        '{"metadata":{"job_id":"tampered"},"signature":"bad"}',
        row["id"] if hasattr(row, "keys") else row[0],
    ),
)
conn.commit()
conn.close()
tampered = requests.get(
    BASE + f"/api/jobs/{job_id}/continuation-metadata", params={"file": body["file"]}
)
assert tampered.status_code == 404
missing = requests.get(BASE + f"/api/jobs/{job_id}/continuation-metadata")
assert missing.status_code == 400
assert missing.json()["error"] == "INVALID_CONTINUATION_METADATA_QUERY"
print({"status": "passed", "signed": True, "verified": True, "tamper_not_accepted": True})
