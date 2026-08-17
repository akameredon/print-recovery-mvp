import sqlite3
import tempfile

import requests
from PIL import Image

from evidence_bundle import build_evidence_bundle, render_handoff_markdown

minimal = build_evidence_bundle(
    job={"id": "demo"},
    manifest={"job": {"source_integrity": "verified"}},
    recovery_report={"generated_at": "now"},
    checkpoints=[{"y_mm": 100}],
    events=[{"event_type": "JOB_CREATED"}],
)
assert minimal["bundle_schema"] == "print-recovery.evidence-handoff/v1"
assert minimal["handoff_status"] == "operator_review_required"
assert minimal["operator_checklist"][0]["complete"] is True
assert minimal["operator_checklist"][1]["complete"] is True
assert minimal["operator_checklist"][3]["complete"] is False
assert "Evidence Handoff Bundle" in render_handoff_markdown(minimal)

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    source = handle.name
Image.new("RGB", (80, 160), "white").save(source)
with open(source, "rb") as image_file:
    created = requests.post(
        BASE + "/api/jobs",
        files={"file": ("bundle.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert created.status_code == 302, created.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute(
    "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
    ("bundle.png",),
).fetchone()[0]
conn.close()
checkpoint = requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint",
    json={"y_mm": 100, "evidence": "acknowledged"},
)
assert checkpoint.status_code == 200, checkpoint.text
bundle = requests.get(BASE + f"/api/jobs/{job_id}/evidence-bundle")
assert bundle.status_code == 200, bundle.text
body = bundle.json()
assert body["bundle_schema"] == "print-recovery.evidence-handoff/v1"
assert body["handoff_status"] == "operator_review_required"
assert body["manifest"]["job"]["source_integrity"] == "verified"
assert body["checkpoints"]
assert body["events"]
assert body["operator_checklist"][0]["complete"] is True
assert body["operator_checklist"][3]["complete"] is False
markdown = requests.get(BASE + f"/api/jobs/{job_id}/evidence-bundle?format=md")
assert markdown.status_code == 200
assert "operator_review_required" in markdown.text
assert "Record operator approval or rejection" in markdown.text
invalid = requests.get(BASE + f"/api/jobs/{job_id}/evidence-bundle?format=xml")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_BUNDLE_FORMAT"
print({"status": "passed", "json": True, "markdown": True, "operator_gates": True})
