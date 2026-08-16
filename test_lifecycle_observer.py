import json
import sqlite3
import tempfile

import requests
from PIL import Image

from lifecycle_observer import observe_lifecycle

valid = observe_lifecycle(
    [
        {"event_type": "JOB_QUEUED", "payload": {"path": "input"}},
        {"event_type": "JOB_STARTED", "payload": {"source": "rip"}},
        {"event_type": "PROGRESS", "payload": {"percent": 50}},
        {"event_type": "JOB_COMPLETED", "payload": {"output": "output"}},
    ]
)
assert valid["status"] == "observed"
assert valid["final_state"] == "completed"
assert valid["event_count"] == 4
assert valid["transitions"][2]["payload"]["percent"] == 50
invalid = observe_lifecycle([{"event_type": "JOB_COMPLETED"}, {"event_type": "PROGRESS"}])
assert invalid["status"] == "invalid"
assert invalid["errors"][0]["code"] == "EVENT_AFTER_TERMINAL_STATE"
unknown = observe_lifecycle([{"event_type": "NOT_A_RIP_EVENT"}])
assert unknown["status"] == "invalid"
assert unknown["errors"][0]["code"] == "UNKNOWN_LIFECYCLE_EVENT"

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = handle.name
Image.new("RGB", (80, 160), "white").save(source)
with open(source, "rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("lifecycle.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("lifecycle.png",),
).fetchone()[0]
conn.close()
events = [
    {"event_type": "JOB_STARTED", "payload": {"queue": "rasterlink"}},
    {"event_type": "PROGRESS", "payload": {"percent": 25}},
    {"event_type": "JOB_COMPLETED", "payload": {"output": "hot-folder"}},
]
observed = requests.post(
    BASE + f"/api/jobs/{job_id}/lifecycle/observe",
    json={"source": "synthetic_rip_observer", "events": events},
)
assert observed.status_code == 200, observed.text
assert observed.json()["observation"]["final_state"] == "completed"
conn = sqlite3.connect("data/print_recovery.sqlite3")
row = conn.execute(
    "SELECT event_type,payload,source FROM events WHERE job_id=? ORDER BY id DESC LIMIT 1",
    (job_id,),
).fetchone()
conn.close()
assert row[0] == "RIP_LIFECYCLE_OBSERVED"
assert row[2] == "synthetic_rip_observer"
assert json.loads(row[1])["events"] == events
bad = requests.post(
    BASE + f"/api/jobs/{job_id}/lifecycle/observe",
    json={"events": [{"event_type": "JOB_COMPLETED"}, {"event_type": "PROGRESS"}]},
)
assert bad.status_code == 400
assert bad.json()["observation"]["errors"][0]["code"] == "EVENT_AFTER_TERMINAL_STATE"
print({"status": "passed", "ordered": True, "invalid_blocked": True, "raw_persisted": True})
