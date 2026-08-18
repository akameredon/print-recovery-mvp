from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet


class SecretStore:
    def __init__(self, root: Path):
        self.path = root / "data" / ".local-secrets.key"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        configured = os.environ.get("PRINT_RECOVERY_MASTER_KEY", "").strip()
        if configured:
            self._key = configured.encode("ascii")
        elif self.path.exists():
            self._key = self.path.read_bytes().strip()
        else:
            self._key = Fernet.generate_key()
            self.path.write_bytes(self._key)
            os.chmod(self.path, 0o600)
        self._fernet = Fernet(self._key)

    def encrypt_json(self, value: dict) -> str:
        return self._fernet.encrypt(json.dumps(value, sort_keys=True).encode()).decode()

    def decrypt_json(self, ciphertext: str | None) -> dict:
        if not ciphertext:
            return {}
        return json.loads(self._fernet.decrypt(ciphertext.encode()).decode())

    def describe(self) -> dict:
        return {
            "encrypted": True,
            "key_source": (
                "environment"
                if os.environ.get("PRINT_RECOVERY_MASTER_KEY")
                else "local_0600_key_file"
            ),
        }
