import tempfile
from pathlib import Path

from trace_archive import archive_trace
from trace_index import index_archives, retrieve_archives

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    archive_trace(
        {
            "events": [
                {"event_type": "JOB_STARTED", "payload": {}},
                {"event_type": "JOB_COMPLETED", "payload": {}},
            ]
        },
        root / "completed.json",
        source="adapter-a",
    )
    archive_trace(
        {
            "events": [
                {"event_type": "JOB_STARTED", "payload": {}},
                {"event_type": "INTERRUPTED", "payload": {"reason": "POWER_LOSS"}},
            ]
        },
        root / "interrupted.json",
        source="adapter-b",
    )
    entries = index_archives(root)
    assert len(entries) == 2
    assert all(entry["hash_verified"] and entry["replay_matches"] for entry in entries)
    assert [entry["path"] for entry in entries] == sorted(entry["path"] for entry in entries)
    completed = retrieve_archives(root, final_state="completed", verified_only=True)
    assert len(completed) == 1
    assert completed[0]["source"] == "adapter-a"
    interrupted = retrieve_archives(root, source="adapter-b")
    assert interrupted[0]["final_state"] == "interrupted"
    (root / "not-an-archive.json").write_text("{}", encoding="utf-8")
    assert len(index_archives(root)) == 2
print({"status": "passed", "indexed": 2, "filters": True, "verified_only": True})
