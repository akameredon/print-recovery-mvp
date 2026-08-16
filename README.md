# Print Recovery State Capture MVP

This is the first local prototype of the software-first recovery assistant. It currently provides a protected job manifest, source hashing, logical checkpoint recording, interruption events, confidence-aware recovery recommendations and assisted continuation generation for image test jobs.

## Run

From this directory:

```bash
python3 app.py
```

Open `http://127.0.0.1:5173` in a browser. Create a test job with an image and media dimensions, record one or more checkpoints, mark an interruption, review the recommendation and generate a continuation image.

## Current status

The prototype is **generated but not printer-validated**. It does not read a real RIP protocol, control a printer, prove physical ink position or guarantee continuation quality. It is intentionally safe and local: no printer-control commands are sent.

## Next integration

Select one exact printer model and RIP workflow. Add an adapter that can observe the actual job or queue events, then compare host-side checkpoints with measured media position during controlled tests.
