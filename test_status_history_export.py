import csv
import io
import sqlite3
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
    sample_path = Path(handle.name)
Image.new("RGB", (40, 40), "white").save(sample_path)

with sample_path.open("rb") as image_file:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": ("export.png", image_file, "image/png")},
        data={"media_width_mm": "100", "media_length_mm": "200"},
        allow_redirects=False,
    )
assert response.status_code == 302, response.text
conn = sqlite3.connect("data/print_recovery.sqlite3")
job_id = conn.execute("SELECT id FROM jobs ORDER BY created_at DESC LIMIT 1").fetchone()[0]
conn.close()
requests.post(BASE + f"/api/jobs/{job_id}/checkpoint", data={"y_mm": "50"})
requests.post(
    BASE + f"/api/jobs/{job_id}/interrupt", json={"event_type": "POWER_OR_PROTECTION_TRIP"}
)

json_export = requests.get(BASE + f"/api/jobs/{job_id}/status-history/export?format=json")
assert json_export.status_code == 200
json_body = json_export.json()
assert json_body["format"] == "json"
assert json_body["total"] == 3
assert [item["to_status"] for item in json_body["items"]] == ["READY", "PRINTING", "INTERRUPTED"]
assert f"{job_id}_status_history.json" in json_export.headers["Content-Disposition"]

csv_export = requests.get(BASE + f"/api/jobs/{job_id}/status-history/export?format=csv")
assert csv_export.status_code == 200
assert csv_export.headers["Content-Type"].startswith("text/csv")
assert f"{job_id}_status_history.csv" in csv_export.headers["Content-Disposition"]
rows = list(csv.DictReader(io.StringIO(csv_export.text)))
assert len(rows) == 3
assert [row["to_status"] for row in rows] == ["READY", "PRINTING", "INTERRUPTED"]

invalid = requests.get(BASE + f"/api/jobs/{job_id}/status-history/export?format=xml")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_EXPORT_FORMAT"

missing = requests.get(BASE + "/api/jobs/not-a-real-job/status-history/export?format=csv")
assert missing.status_code == 404
assert missing.json()["error"] == "JOB_NOT_FOUND"
print(
    {
        "status": "passed",
        "job_id": job_id,
        "json_items": len(json_body["items"]),
        "csv_rows": len(rows),
    }
)
