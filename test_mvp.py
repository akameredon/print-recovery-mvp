from pathlib import Path

import requests
from PIL import Image, ImageDraw

BASE = "http://127.0.0.1:5173"
root = Path(__file__).resolve().parent
sample = root / "sample_test_job.png"
img = Image.new("RGB", (800, 600), "white")
draw = ImageDraw.Draw(img)
draw.rectangle((30, 30, 770, 570), outline="navy", width=8)
draw.line((30, 300, 770, 300), fill="red", width=4)
draw.text((60, 80), "PRINT RECOVERY TEST JOB", fill="black")
img.save(sample)

with sample.open("rb") as fh:
    response = requests.post(
        BASE + "/api/jobs",
        files={"file": (sample.name, fh, "image/png")},
        data={
            "printer_model": "Prototype test printer",
            "rip_name": "Prototype test RIP",
            "media_width_mm": "400",
            "media_length_mm": "300",
            "resolution": "test",
            "passes": "4",
            "profile": "test-profile",
        },
        allow_redirects=False,
    )
assert response.status_code == 302, response.text

html = requests.get(BASE + "/").text
marker = 'data-job="'
job_id = html.split(marker, 1)[1].split('"', 1)[0]

assert requests.post(
    BASE + f"/api/jobs/{job_id}/checkpoint",
    json={"y_mm": 150, "band_mm": 5, "evidence": "transmitted"},
).ok
assert requests.post(
    BASE + f"/api/jobs/{job_id}/interrupt", json={"event_type": "POWER_OR_PROTECTION_TRIP"}
).ok
recommendation = requests.get(BASE + f"/api/jobs/{job_id}/recommendation").json()
assert recommendation["recommendation"] == "TEST_FIRST"
continuation = requests.post(
    BASE + f"/api/jobs/{job_id}/continuation", json={"y_mm": 150, "overlap_mm": 5}
)
assert continuation.ok, continuation.text
output = root / "outputs" / continuation.json()["file"]
assert output.exists() and output.stat().st_size > 0
print({"job_id": job_id, "recommendation": recommendation, "continuation": str(output)})
