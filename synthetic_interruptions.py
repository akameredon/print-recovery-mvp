from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from PIL import Image

INTERRUPTION_SCENARIOS = {
    "POWER_LOSS": "outage",
    "PROTECTION_TRIP": "outage",
    "PRINTER_ERROR": "crash",
    "OPERATOR_ABORT": "abort",
    "COMMUNICATION_LOSS": "communication_loss",
    "MATERIAL_ISSUE": "material_issue",
    "UNKNOWN": "unknown",
}


def _create_job(base_url: str, name: str, image_path: Path) -> tuple[str, str]:
    with image_path.open("rb") as image_file:
        response = requests.post(
            base_url + "/api/jobs",
            files={"file": (name, image_file, "image/png")},
            data={"media_width_mm": "100", "media_length_mm": "200"},
            allow_redirects=False,
        )
    assert response.status_code == 302, response.text
    import sqlite3

    conn = sqlite3.connect("data/print_recovery.sqlite3")
    row = conn.execute(
        "SELECT id,source_path FROM jobs WHERE file_name=? ORDER BY created_at DESC LIMIT 1",
        (name,),
    ).fetchone()
    conn.close()
    assert row, f"job was not persisted for {name}"
    return row[0], row[1]


def _checkpoint(base_url: str, job_id: str) -> None:
    response = requests.post(
        base_url + f"/api/jobs/{job_id}/checkpoint",
        json={"y_mm": 100, "evidence": "acknowledged"},
    )
    assert response.status_code == 200, response.text


def run_synthetic_suite(base_url: str = "http://127.0.0.1:5173") -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="print-recovery-day50-") as temp_dir:
        image_path = Path(temp_dir) / "synthetic.png"
        Image.new("RGB", (80, 160), "white").save(image_path)
        for reason, expected_classification in INTERRUPTION_SCENARIOS.items():
            name = f"synthetic-{reason.lower()}.png"
            job_id, _ = _create_job(base_url, name, image_path)
            _checkpoint(base_url, job_id)
            interrupted = requests.post(
                base_url + f"/api/jobs/{job_id}/interrupt",
                json={"reason": reason, "note": f"Synthetic {reason.lower()} scenario"},
            )
            assert interrupted.status_code == 200, interrupted.text
            classification = interrupted.json()["classification"]["classification"]
            assert classification == expected_classification, interrupted.text
            report = requests.get(base_url + f"/api/jobs/{job_id}/recovery-report")
            assert report.status_code == 200, report.text
            assert (
                report.json()["interruption"]["details"]["classification"]["classification"]
                == expected_classification
            )
            results.append(
                {"scenario": reason, "status": "passed", "classification": classification}
            )

        successful_job, _ = _create_job(base_url, "synthetic-success.png", image_path)
        _checkpoint(base_url, successful_job)
        interrupted = requests.post(
            base_url + f"/api/jobs/{successful_job}/interrupt",
            json={"reason": "POWER_LOSS", "note": "Synthetic successful recovery"},
        )
        assert interrupted.status_code == 200, interrupted.text
        continuation = requests.post(
            base_url + f"/api/jobs/{successful_job}/continuation",
            json={"y_mm": 100, "overlap_mm": 5},
        )
        assert continuation.status_code == 200, continuation.text
        assert continuation.json()["file"].startswith("continuation-v001_")
        results.append({"scenario": "SUCCESSFUL_ASSISTED_RECOVERY", "status": "passed"})

        blocked_checkpoint_job, _ = _create_job(base_url, "synthetic-no-checkpoint.png", image_path)
        blocked = requests.post(
            base_url + f"/api/jobs/{blocked_checkpoint_job}/continuation",
            json={"y_mm": 100},
        )
        assert blocked.status_code == 409, blocked.text
        assert "CHECKPOINT_MISSING" in {
            item["code"] for item in blocked.json()["recovery_safety"]["blockers"]
        }
        results.append({"scenario": "MISSING_CHECKPOINT", "status": "passed", "blocked": True})

        changed_job, source_path = _create_job(base_url, "synthetic-changed-source.png", image_path)
        _checkpoint(base_url, changed_job)
        with open(source_path, "ab") as changed_file:
            changed_file.write(b"synthetic-change")
        changed = requests.post(
            base_url + f"/api/jobs/{changed_job}/continuation",
            json={"y_mm": 100},
        )
        assert changed.status_code == 409, changed.text
        assert "SOURCE_CHANGED" in {
            item["code"] for item in changed.json()["recovery_safety"]["blockers"]
        }
        results.append({"scenario": "CHANGED_SOURCE", "status": "passed", "blocked": True})

    return {
        "suite": "day50_synthetic_interruptions",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "scenario_count": len(results),
        "source": "synthetic local API workflow",
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Day 50 synthetic interruption suite")
    parser.add_argument("--base-url", default="http://127.0.0.1:5173")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = run_synthetic_suite(args.base_url)
    serialized = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
