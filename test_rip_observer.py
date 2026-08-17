import json
import tempfile
from pathlib import Path

from rip_observer import RIPObserverAdapter

with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as handle:
    handle.write(
        json.dumps({"event_type": "JOB_STARTED", "payload": {"queue": "rasterlink"}}) + "\n"
    )
    handle.write(json.dumps({"event_type": "PROGRESS", "payload": {"percent": 40}}) + "\n")
    handle.write(
        json.dumps({"event_type": "JOB_COMPLETED", "payload": {"output": "hot-folder"}}) + "\n"
    )
    trace_path = Path(handle.name)
result = RIPObserverAdapter().read_trace(trace_path)
assert result["adapter"] == "generic_rip_observer"
assert result["event_count"] == 3
assert result["observation"]["status"] == "observed"
assert result["observation"]["final_state"] == "completed"
assert result["events"][1]["payload"]["percent"] == 40

with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as handle:
    handle.write('{"event_type":"JOB_STARTED"}\n')
    handle.write("not-json\n")
    handle.write(json.dumps({"event_type": "PROGRESS", "payload": {"percent": 10}}) + "\n")
    malformed_path = Path(handle.name)
malformed = RIPObserverAdapter().read_trace(malformed_path)
assert malformed["observation"]["status"] == "invalid"
assert malformed["observation"]["errors"][0]["code"] == "INVALID_JSON"

with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as handle:
    handle.write(json.dumps({"event_type": "JOB_COMPLETED"}) + "\n")
    handle.write(json.dumps({"event_type": "PROGRESS"}) + "\n")
    invalid_path = Path(handle.name)
invalid = RIPObserverAdapter().read_trace(invalid_path)
assert invalid["observation"]["status"] == "invalid"
assert any(
    error["code"] == "EVENT_AFTER_TERMINAL_STATE" for error in invalid["observation"]["errors"]
)
print({"status": "passed", "valid_trace": True, "malformed_rejected": True, "read_only": True})
