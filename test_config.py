import json
import os
import tempfile
from pathlib import Path

from config import DEFAULTS, load_config, resolve_path

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    assert load_config(root) == DEFAULTS
    config_path = root / "custom.json"
    config_path.write_text(json.dumps({"port": 6123, "log_level": "debug", "data_dir": "runtime-data"}), encoding="utf-8")
    os.environ["PRINT_RECOVERY_CONFIG"] = str(config_path)
    os.environ["PRINT_RECOVERY_MAX_UPLOAD_MB"] = "25"
    loaded = load_config(root)
    assert loaded["port"] == 6123
    assert loaded["log_level"] == "DEBUG"
    assert loaded["max_upload_mb"] == 25
    assert resolve_path(root, loaded["data_dir"]) == root / "runtime-data"
    del os.environ["PRINT_RECOVERY_CONFIG"]
    del os.environ["PRINT_RECOVERY_MAX_UPLOAD_MB"]
print({"status": "passed", "default_port": DEFAULTS["port"], "override_port": 6123, "override_upload_mb": 25})
