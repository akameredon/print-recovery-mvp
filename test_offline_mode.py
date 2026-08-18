from offline_mode import ConnectivityState

state = ConnectivityState()
assert state.snapshot()["mode"] == "offline"
assert state.snapshot()["capture_available"] is True
assert state.snapshot()["network_required_for_capture"] is False
assert state.set_mode("reconnecting")["reconnect_attempt"] == 1
assert state.set_mode("reconnecting")["reconnect_attempt"] == 2
assert state.set_mode("online")["reconnect_attempt"] == 0
try:
    state.set_mode("broken")
except ValueError as error:
    assert "offline, online or reconnecting" in str(error)
else:
    raise AssertionError("invalid connectivity mode was accepted")
print({"status": "passed", "offline_capture": True, "reconnect_backoff_state": True})
