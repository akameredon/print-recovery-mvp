import sqlite3
import tempfile
import uuid
from pathlib import Path

import requests
from PIL import Image

BASE = "http://127.0.0.1:5173"
TOKEN = f"day22-{uuid.uuid4().hex[:10]}"


def create_job(name, printer):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        source = Path(handle.name)
    Image.new("RGB", (30, 30), "white").save(source)
    with source.open("rb") as image_file:
        response = requests.post(
            BASE + "/api/jobs",
            files={"file": (name, image_file, "image/png")},
            data={
                "printer_model": printer,
                "rip_name": "SearchRIP 2.0",
                "media_width_mm": "100",
                "media_length_mm": "200",
            },
            allow_redirects=False,
        )
    assert response.status_code == 302, response.text
    conn = sqlite3.connect("data/print_recovery.sqlite3")
    job_id = conn.execute(
        "SELECT id FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1", (name,)
    ).fetchone()[0]
    conn.close()
    return job_id


mimaki_name = f"{TOKEN}-mimaki-banner.png"
roland_name = f"{TOKEN}-retail-poster.png"
mimaki_printer = f"Mimaki {TOKEN}"
roland_printer = f"Roland {TOKEN}"
mimaki_id = create_job(mimaki_name, mimaki_printer)
roland_id = create_job(roland_name, roland_printer)
conn = sqlite3.connect("data/print_recovery.sqlite3")
conn.execute(
    "UPDATE jobs SET created_at='2099-01-15T10:00:00+00:00', updated_at='2099-01-15T10:00:00+00:00' WHERE id=?",
    (mimaki_id,),
)
conn.execute(
    "UPDATE jobs SET created_at='2099-02-15T10:00:00+00:00', updated_at='2099-02-02T10:00:00+00:00' WHERE id=?",
    (roland_id,),
)
conn.commit()
conn.close()

by_file = requests.get(BASE + f"/api/jobs?q={TOKEN}-mimaki-banner.png")
assert by_file.status_code == 200
assert [job["file_name"] for job in by_file.json()["jobs"]] == [mimaki_name]
assert by_file.json()["jobs"][0]["id"] == mimaki_id
by_printer = requests.get(BASE + f"/api/jobs?q={roland_printer}")
assert by_printer.status_code == 200
assert [job["file_name"] for job in by_printer.json()["jobs"]] == [roland_name]
assert by_printer.json()["jobs"][0]["id"] == roland_id
by_id = requests.get(BASE + f"/api/jobs?q={mimaki_id[:8]}")
assert by_id.status_code == 200
assert mimaki_id in {job["id"] for job in by_id.json()["jobs"]}
by_date = requests.get(BASE + "/api/jobs?date_from=2099-02-01&date_to=2099-02-28")
assert by_date.status_code == 200
assert roland_id in {job["id"] for job in by_date.json()["jobs"]}
combined = requests.get(BASE + f"/api/jobs?filter=active&q={mimaki_printer}&date_from=2099-01-01")
assert combined.status_code == 200
assert [job["file_name"] for job in combined.json()["jobs"]] == [mimaki_name]

html = requests.get(BASE + f"/?q={TOKEN}-mimaki&date_from=2099-01-01")
assert html.status_code == 200
assert mimaki_name in html.text
assert roland_name not in html.text

invalid = requests.get(BASE + "/api/jobs?date_from=2099/01/01")
assert invalid.status_code == 400
assert invalid.json()["error"] == "INVALID_JOB_QUERY"
invalid_range = requests.get(BASE + "/api/jobs?date_from=2099-03-01&date_to=2099-01-01")
assert invalid_range.status_code == 200
assert invalid_range.json()["count"] == 0
print(
    {
        "status": "passed",
        "matches": ["file_name", "printer_model", "job_id", "date"],
        "combined": True,
    }
)
