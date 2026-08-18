import io

import app as application

application.UPLOAD_ATTEMPTS.clear()
application.CONFIG["upload_rate_limit_per_minute"] = 2
application.CONFIG["max_upload_mb"] = 1
client = application.app.test_client()

invalid_extension = client.post(
    "/api/jobs",
    data={"file": (io.BytesIO(b"x"), "unsafe.exe", "application/octet-stream")},
    content_type="multipart/form-data",
)
assert invalid_extension.status_code == 400
assert invalid_extension.get_json()["error"] == "INVALID_UPLOAD_TYPE"
invalid_mime = client.post(
    "/api/jobs",
    data={"file": (io.BytesIO(b"x"), "mime.png", "text/plain")},
    content_type="multipart/form-data",
)
assert invalid_mime.status_code == 400
assert invalid_mime.get_json()["error"] == "INVALID_UPLOAD_TYPE"
application.UPLOAD_ATTEMPTS.clear()
application.CONFIG["upload_rate_limit_per_minute"] = 2
first = client.post(
    "/api/jobs",
    data={"file": (io.BytesIO(b"one"), "rate-one.png", "image/png")},
    content_type="multipart/form-data",
)
second = client.post(
    "/api/jobs",
    data={"file": (io.BytesIO(b"two"), "rate-two.png", "image/png")},
    content_type="multipart/form-data",
)
third = client.post(
    "/api/jobs",
    data={"file": (io.BytesIO(b"three"), "rate-three.png", "image/png")},
    content_type="multipart/form-data",
)
assert first.status_code == 302, first.get_data(as_text=True)
assert second.status_code == 302, second.get_data(as_text=True)
assert third.status_code == 429
assert third.get_json()["error"] == "UPLOAD_RATE_LIMITED"
assert third.headers["Retry-After"]
application.UPLOAD_ATTEMPTS.clear()
application.CONFIG["upload_rate_limit_per_minute"] = 100
print({"status": "passed", "invalid_extension": True, "invalid_mime": True, "rate_limited": True})
