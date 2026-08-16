from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULTS: dict[str, Any] = {
    "data_dir": "data",
    "output_dir": "outputs",
    "log_level": "INFO",
    "host": "127.0.0.1",
    "port": 5173,
    "max_upload_mb": 100,
}


def load_config(root: Path) -> dict[str, Any]:
    """Load optional local JSON configuration without requiring setup."""
    config = dict(DEFAULTS)
    config_path = Path(os.getenv("PRINT_RECOVERY_CONFIG", root / "config.json"))
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError("Configuration must be a JSON object")
        config.update(loaded)

    env_map = {
        "PRINT_RECOVERY_DATA_DIR": "data_dir",
        "PRINT_RECOVERY_OUTPUT_DIR": "output_dir",
        "PRINT_RECOVERY_LOG_LEVEL": "log_level",
        "PRINT_RECOVERY_HOST": "host",
        "PRINT_RECOVERY_PORT": "port",
        "PRINT_RECOVERY_MAX_UPLOAD_MB": "max_upload_mb",
    }
    for env_name, key in env_map.items():
        if env_name in os.environ:
            config[key] = os.environ[env_name]

    config["port"] = int(config["port"])
    config["max_upload_mb"] = int(config["max_upload_mb"])
    config["log_level"] = str(config["log_level"]).upper()
    if config["port"] < 1 or config["port"] > 65535:
        raise ValueError("port must be between 1 and 65535")
    if config["max_upload_mb"] < 1:
        raise ValueError("max_upload_mb must be positive")
    return config


def resolve_path(root: Path, configured: str) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else root / path
