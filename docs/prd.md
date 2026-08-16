---
title: Product Requirements Document
project: print-recovery-project
version: 1.0.0
status: approved-draft
owner: Macdonald Akadonye
last_updated: 2026-08-16
tags:
  - prd
  - product
  - recovery
sources:
  - https://mimaki.com/manual/raster-link7/reference_guide/en-US/325555339.html
  - https://docs.duet3d.com/User_manual/Tuning/Resume
---

# Product Requirements Document

## Product summary

Print Recovery State Capture System is a software companion for large-format print workflows. It captures job metadata, logical progress checkpoints and interruption events, then provides a recovery report and continuation workflow after an outage, protection trip, software crash or communication failure.

## Target users

The primary users are large-format print operators who need to save jobs and avoid manual alignment. Print technicians configure integrations and investigate edge cases. Shop owners review waste, downtime and recovery trends. RIP or printer integrators may develop adapters.

## Core user journey

The operator starts a job through the existing RIP. The system captures the job manifest and records progress. If the printer stops unexpectedly, the original job is preserved and the system displays the last prepared, transmitted, acknowledged and physically confirmed points. The operator reviews the confidence status, runs a registration test if needed, approves a continuation job and records the result.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| PRD-001 | Create a unique job ID and immutable job manifest | Must |
| PRD-002 | Capture source file hash, printer, media, origin, scale, resolution, pass count and colour profile | Must |
| PRD-003 | Record fine-grained logical progress checkpoints | Must |
| PRD-004 | Detect unexpected stop, communication loss, RIP crash or manual abort | Must |
| PRD-005 | Preserve the last known state before interruption | Must |
| PRD-006 | Display confidence categories for prepared, transmitted, acknowledged and physically confirmed progress | Must |
| PRD-007 | Generate a recovery report after reboot | Must |
| PRD-008 | Generate a partial continuation job with controlled overlap | Must |
| PRD-009 | Provide operator approval before assisted continuation | Must |
| PRD-010 | Support certified adapters only after model-specific validation | Must |
| PRD-011 | Keep a history of recovery decisions and operator overrides | Should |
| PRD-012 | Calculate material saved and interruption trends | Could |

## Non-functional requirements

The application should impose negligible workflow delay, persist checkpoints safely even if the host restarts, remain usable by non-technical operators, work offline, protect job records from unauthorized modification and isolate printer integrations through adapters.

## Scope exclusions

Version 1 excludes electrical hardware, UPS functions, automatic mechanical repositioning, firmware modification, universal compatibility, unverified printer-control commands and cloud-only operation.

## Product risks

The product may not receive enough telemetry from some printers. Printer buffering may make “last data sent” different from “last ink printed.” Media can shift during a trip, and different media or ink modes can change acceptable overlap. The interface must expose uncertainty rather than conceal it.
