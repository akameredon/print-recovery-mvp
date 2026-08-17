from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lifecycle_observer import observe_lifecycle


class RIPObserverAdapter:
    """Read-only observer for a vendor-neutral JSON Lines RIP trace."""

    name = "generic_rip_observer"

    def read_trace(self, trace_path: Path) -> dict[str, Any]:
        events: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        with trace_path.open("r", encoding="utf-8") as trace_file:
            for line_number, line in enumerate(trace_file, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    errors.append(
                        {"line": line_number, "code": "INVALID_JSON", "message": str(error)}
                    )
                    continue
                if not isinstance(record, dict):
                    errors.append({"line": line_number, "code": "TRACE_RECORD_NOT_OBJECT"})
                    continue
                events.append(record)
        observation = observe_lifecycle(events)
        if errors:
            observation = {
                **observation,
                "status": "invalid",
                "errors": errors + observation["errors"],
            }
        return {
            "adapter": self.name,
            "trace_path": str(trace_path),
            "event_count": len(events),
            "events": events,
            "observation": observation,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read a JSON Lines RIP observer trace")
    parser.add_argument("trace_path", type=Path)
    args = parser.parse_args()
    print(json.dumps(RIPObserverAdapter().read_trace(args.trace_path), indent=2))


if __name__ == "__main__":
    main()
