---
title: Technical Design Specification
project: print-recovery-project
version: 1.0.0
status: approved-draft
owner: Macdonald Akadonye
last_updated: 2026-08-16
tags:
  - architecture
  - technical-design
sources:
  - https://mimaki.com/manual/raster-link7/reference_guide/en-US/325555339.html
  - https://docs.duet3d.com/User_manual/Tuning/Resume
---

# Technical Design Specification

## System overview

The system is a local Windows application that sits beside an existing RIP and printer workflow. It observes job events, creates an immutable job manifest, records logical checkpoints and stores interruption events. A recovery advisor calculates the best available continuation point and a continuation generator creates a partial job using the original coordinate system.

## Components

| Component | Responsibility |
|---|---|
| Job Monitor | Ingest job lifecycle, hot-folder, queue, RIP and adapter events |
| Manifest Service | Store source hash, settings, media geometry and integration identity |
| Checkpoint Engine | Normalize progress into bands, passes, tiles or coordinates and persist snapshots |
| Event Store | Append raw events with timestamps and source metadata |
| Interruption Detector | Classify expected and unexpected stops |
| Recovery Advisor | Calculate confidence categories, candidate points and warnings |
| Continuation Generator | Crop or mask the original job and create a partial output |
| Operator UI | Display active, interrupted and completed jobs and guide decisions |
| Adapter Layer | Isolate printer/RIP-specific integrations and conformance tests |
| Audit Reporter | Export recovery history, outcome and estimated material saved |

## Recovery state model

A job moves from `READY` to `PRINTING`, then to `COMPLETED`, `PAUSED`, `INTERRUPTED` or `FAILED`. An interrupted job moves to `ANALYSING`, `AWAITING_APPROVAL`, `CONTINUING`, `RECOVERED` or `SCRAPPED`. State transitions are append-only and include the actor and evidence source.

## Recovery principle

The system stores separate positions for prepared, transmitted, acknowledged and physically confirmed progress. It never treats the last host transmission as automatically equal to physical output. A certified adapter may promote a status to higher confidence only after passing model-specific tests.

## Integration modes

Monitoring Mode watches files and logs. Assisted Recovery Mode generates a continuation and uses a registration test or operator-confirmed boundary. Certified Recovery Mode uses a validated adapter with reliable status or position data. The system should begin with Monitoring and Assisted modes for one target machine.

## Safety boundary

No component bypasses printer safety, electrical protection, emergency stops or manufacturer procedures. Undocumented mechanical control commands are prohibited in v1. The software can recommend restart when safe recovery cannot be supported.
