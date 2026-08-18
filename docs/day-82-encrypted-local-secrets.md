# Day 82 — Encrypted local secrets and configuration

**Status:** Implemented and verified.

Day 82 adds encrypted local secret storage for adapter configurations. Secret values are accepted only through the explicit `secrets` field, encrypted with Fernet before persistence, and stored separately from ordinary adapter settings. Secrets embedded in public `settings` remain rejected to prevent accidental plaintext storage.

The local encryption key is supplied by `PRINT_RECOVERY_MASTER_KEY` when configured. Otherwise, the application creates `data/.local-secrets.key` with filesystem mode `0600`. The key file is not returned by APIs, and the public adapter response exposes only `{encrypted: true, plaintext_returned: false}` metadata. Plaintext secret values are never included in API responses or the ordinary settings JSON.

Migration 15 adds the encrypted ciphertext column without exposing or migrating plaintext values. Existing adapter configurations remain compatible, and legacy plaintext-secret submissions continue to return `SECRET_NOT_ALLOWED`.

| Verification | Result |
|---|---|
| Encrypted secret persistence | Passed |
| Plaintext exclusion from API and SQLite settings | Passed |
| 0600 local key-file permissions | Passed |
| Legacy plaintext-secret rejection | Passed |
| Black, Ruff and compilation | Passed |
| Non-restart regression suite | Passed; 70 tests |

The focused regression test is `test_encrypted_secrets.py`.

> Encryption protects local stored configuration from ordinary disclosure. It does not replace operating-system permissions, key backup, key rotation procedures or a dedicated secrets manager for a production deployment.
