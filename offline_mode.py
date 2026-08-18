from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConnectivityState:
    mode: str = "offline"
    reconnect_attempt: int = 0

    def set_mode(self, mode: str) -> dict:
        if mode not in {"offline", "online", "reconnecting"}:
            raise ValueError("mode must be offline, online or reconnecting")
        self.mode = mode
        self.reconnect_attempt = 0 if mode == "online" else self.reconnect_attempt + 1
        return self.snapshot()

    def snapshot(self) -> dict:
        return {
            "mode": self.mode,
            "capture_available": True,
            "network_required_for_capture": False,
            "reconnect_attempt": self.reconnect_attempt,
            "reconnect_strategy": "local capture continues; optional integrations retry after reconnect",
        }
