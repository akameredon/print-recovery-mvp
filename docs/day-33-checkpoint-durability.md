# Day 33 — Atomic checkpoint writes and process-kill recovery

## Purpose

Day 33 strengthens checkpoint durability for interruptions such as power loss or protection trips. Each checkpoint write, its status-history transition and its `CHECKPOINT` event are committed through the same SQLite transaction. The application database connection now uses a five-second busy timeout, foreign-key enforcement, WAL journaling and `FULL` synchronous mode.

These settings reduce the risk of a partially recorded checkpoint and ensure that committed evidence is durable before the request completes. They do not claim that an uncommitted transaction can be recovered after a process is killed; the correct safety behavior is to recover the last committed state.

## Recovery behavior

After a process termination, the application reopens the same SQLite database and runs the normal migration check. The last committed checkpoint remains available through the job detail endpoint, and its corresponding event remains in the timeline. An interrupted write that never committed is not presented as confirmed evidence.

## Verification

```bash
python3 test_checkpoint_durability.py
```

The test records a checkpoint with band and pass evidence, terminates the Flask process, starts a new process and verifies the checkpoint and `CHECKPOINT` event after restart. The rest of the executable regression suite was run in a separate server session because this specific test intentionally terminates the server during its lifecycle; all tests passed.
