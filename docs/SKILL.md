---
name: print-recovery-state-capture
description: Software-first recovery workflows for large-format printer jobs after power loss, storm-related protection trips, RIP crashes, communication failures or manual stops. Use when capturing print-job state, designing checkpointing, reviewing PRDs/SRS documents, building RIP/printer adapters, generating continuation jobs, validating resume accuracy, or documenting this project.
---

# Print Recovery State Capture

## Purpose

Use this skill to design, document and validate a software companion that preserves large-format print jobs and guides accurate continuation after an unexpected interruption. Keep the workflow local-first and printer/RIP-specific.

## Non-negotiable technical boundary

Never equate the last data transmitted by a RIP or host computer with the last physical ink printed. Printers may buffer data, lose internal state, shift media or stop between transmission and deposition. Always report these evidence levels separately:

| Evidence level | Meaning |
|---|---|
| Prepared | Job/raster data exists locally |
| Transmitted | Data was sent through the interface |
| Acknowledged | Printer or protocol confirmed receipt/progress |
| Physically confirmed | Reliable printer position or controlled operator test confirms the boundary |

Enable automatic or certified recovery only when the named printer/RIP adapter has passed repeatable tests. Otherwise use assisted recovery with a registration strip, operator-confirmed boundary and conservative overlap.

## Required workflow

1. Identify the exact printer model, RIP software/version, connection method, media, print mode and available logs or APIs.
2. Preserve the original source file and compute a stable hash. Capture media geometry, origin, scale, resolution, pass count, colour profile and layout.
3. Define the logical checkpoint unit. Prefer raster bands, passes, media-advance increments or tiles over the vague phrase “bit-by-bit.” Store coordinate, timestamp, evidence source and state hash.
4. Append raw job, RIP, printer, communication and operator events. Persist checkpoints atomically and never mark a failed write as safe.
5. Detect unexpected stop conditions, but distinguish power loss, communication loss, RIP crash, manual abort, media end and normal completion when evidence allows.
6. After restart, verify job identity and critical settings. Calculate last prepared, transmitted, acknowledged and physically confirmed points.
7. Recommend one of three outcomes: **continue**, **test first**, or **restart**. Prefer “test first” when physical position is uncertain.
8. Generate a continuation job in the original coordinate system. Preserve scale, origin, print settings and a printer-specific overlap. Never overwrite the original job.
9. Require operator approval unless certified recovery is enabled for that exact adapter. Record the decision, test result, outcome, seam quality and material saved.
10. Expand compatibility only after the first printer/RIP combination passes controlled interruption tests at multiple positions.

## Architecture guidance

Use separate modules for Job Monitor, Manifest Service, Checkpoint Engine, Event Store, Interruption Detector, Recovery Advisor, Continuation Generator, Operator UI, Adapter Layer and Audit Reporter. Keep printer-specific logic inside versioned adapters. The core recovery engine must not assume a particular brand or protocol.

## Safety and refusal rules

Do not bypass electrical breakers, residual-current devices, surge protection, emergency stops, printer interlocks or manufacturer procedures. Do not issue undocumented mechanical commands to a production printer. Do not claim universal compatibility, zero-waste recovery or exact physical positioning without validation. Recommend restart when the source file is missing, settings conflict, checkpoint persistence failed, media shifted materially, the printer origin is unknown or the adapter cannot establish adequate confidence.

## Documentation standards

When creating project documents, distinguish **concept**, **draft**, **generated**, **verified** and **complete**. Do not describe content as saved unless an actual file exists. Do not describe a file pack as ready until the required files are written, packaged and inspected. Preserve raw evidence separately from edited documents, keep dated revisions and include source references for external claims.

## Validation minimum

For each supported printer/RIP combination, test normal completion, controlled pause, interruption before transmission, interruption during transmission, printer-side stop, host restart, missing telemetry and settings mismatch. Measure predicted coordinate, actual continuation alignment, seam visibility, colour consistency, media saved and operator recovery time. Certified mode is not complete until results are repeatable.
