from __future__ import annotations

from pathlib import Path
from typing import Any


def build_job_manifest(
    job: dict[str, Any],
    *,
    source_exists: bool,
    actual_hash: str | None,
    captured_at: str,
    capture_mode: str = "source_upload",
) -> dict[str, Any]:
    expected_hash = job.get("source_hash")
    integrity = (
        "missing"
        if not source_exists
        else ("verified" if actual_hash == expected_hash else "changed")
    )
    return {
        "manifest_schema": "print-recovery.job-manifest/v1",
        "captured_at": captured_at,
        "capture_mode": capture_mode,
        "job": {
            "id": job.get("id"),
            "file_name": job.get("file_name"),
            "source_path": str(Path(job.get("source_path", ""))),
            "source_hash": expected_hash,
            "actual_source_hash": actual_hash,
            "source_integrity": integrity,
        },
        "printer": {
            "model": job.get("printer_model"),
            "rip": job.get("rip_name"),
            "orientation": job.get("orientation"),
        },
        "media": {
            "width_mm": job.get("media_width_mm"),
            "length_mm": job.get("media_length_mm"),
            "origin_x_mm": job.get("origin_x_mm"),
            "origin_y_mm": job.get("origin_y_mm"),
            "overlap_mm": job.get("overlap_mm"),
            "scale": job.get("scale"),
            "resolution": job.get("resolution"),
            "passes": job.get("passes"),
            "profile": job.get("profile"),
        },
        "recovery_mode": "assisted_only",
    }
