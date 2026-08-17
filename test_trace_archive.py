import json
import tempfile
from pathlib import Path

from trace_archive import archive_trace, replay_archive

observed = {
    "events": [
        {"event_type": "JOB_STARTED", "payload": {"queue": "rasterlink"}},
        {"event_type": "PROGRESS", "payload": {"percent": 60}},
        {"event_type": "JOB_COMPLETED", "payload": {"output": "hot-folder"}},
    ]
}
with tempfile.TemporaryDirectory() as temp_dir:
    archive_path = Path(temp_dir) / "observer-trace.json"
    archive = archive_trace(observed, archive_path)
    assert archive["archive_schema"] == "print-recovery.observer-trace/v1"
    assert len(archive["archive_sha256"]) == 64
    replay = replay_archive(archive_path)
    assert replay["hash_verified"] is True
    assert replay["replay_matches"] is True

    tampered = json.loads(archive_path.read_text(encoding="utf-8"))
    tampered["events"][1]["payload"]["percent"] = 61
    archive_path.write_text(json.dumps(tampered), encoding="utf-8")
    tampered_result = replay_archive(archive_path)
    assert tampered_result["hash_verified"] is False
    assert tampered_result["replay_matches"] is False
print(
    {
        "status": "passed",
        "archive_hash": True,
        "deterministic_replay": True,
        "tamper_detected": True,
    }
)
