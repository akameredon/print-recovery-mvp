import os
import sqlite3
import time

import requests

from app import SESSION_TTL_SECONDS, session_is_expired

BASE = "http://127.0.0.1:5173"
client = requests.Session()
prefix = f"day62_{os.getpid()}"
password = "correct-horse-123"

created = client.post(
    BASE + "/api/users",
    json={
        "username": prefix,
        "display_name": "Day 62 Authentication",
        "role": "operator",
        "password": password,
    },
)
assert created.status_code == 201, created.text
user_id = created.json()["user"]["id"]

conn = sqlite3.connect("data/print_recovery.sqlite3")
hash_value = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()[0]
conn.close()
assert hash_value
assert hash_value != password
assert hash_value.startswith("scrypt:") or hash_value.startswith("pbkdf2:")

wrong = client.post(BASE + "/api/session", json={"username": prefix, "password": "wrong-password"})
assert wrong.status_code == 401
assert wrong.json()["error"] == "INVALID_CREDENTIALS"

login = client.post(BASE + "/api/login", json={"username": prefix, "password": password})
assert login.status_code == 200
assert login.json()["authenticated"] is True
assert login.json()["expires_in_seconds"] == SESSION_TTL_SECONDS

current = client.get(BASE + "/api/session")
assert current.status_code == 200
assert current.json()["authenticated"] is True
assert current.json()["user"]["id"] == user_id

logout = client.delete(BASE + "/api/session")
assert logout.status_code == 200
assert logout.json()["authenticated"] is False

now_epoch = time.time()
assert session_is_expired(str(now_epoch - SESSION_TTL_SECONDS - 1), now_epoch=now_epoch)
assert not session_is_expired(str(now_epoch - 1), now_epoch=now_epoch)
assert session_is_expired(None, now_epoch=now_epoch)
print({"status": "passed", "hash_not_plaintext": True, "login": True, "expiry": True})
