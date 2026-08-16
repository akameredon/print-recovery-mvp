---
title: Software Requirements Specification
project: print-recovery-project
version: 1.0.0
status: approved-draft
owner: Macdonald Akadonye
last_updated: 2026-08-16
tags:
  - srs
  - requirements
sources:
  - https://mimaki.com/manual/raster-link7/reference_guide/en-US/325555339.html
  - https://docs.duet3d.com/User_manual/Tuning/Resume
---

# Software Requirements Specification

## Purpose and scope

This specification defines a software system that captures large-format print progress and interruption metadata, then generates a precise recovery recommendation or continuation workflow. The system is a companion layer around an existing RIP and printer. It does not guarantee perfect visual restoration when the printer’s physical state is unavailable.

## Operating environment

The initial deployment is a Windows workstation located in the print shop, with local storage and optional access to the shop network. The system may observe RIP hot folders, print queues, supported logs or vendor-approved interfaces. Linux or local-server deployment may be added later.

## Functional requirements

| ID | Requirement |
|---|---|
| SRS-F-001 | The system shall assign a unique ID to every monitored job. |
| SRS-F-002 | The system shall store source-file hash, file name, printer profile, media, dimensions, origin, scale, resolution, pass count and colour profile where available. |
| SRS-F-003 | The system shall persist checkpoints at a configured interval or logical band boundary. |
| SRS-F-004 | The system shall record job lifecycle, RIP, communication and printer-status events. |
| SRS-F-005 | The system shall detect unexpected stops and classify their source when evidence exists. |
| SRS-F-006 | The system shall preserve the last durable state before interruption. |
| SRS-F-007 | The system shall distinguish prepared, transmitted, acknowledged and physically confirmed progress. |
| SRS-F-008 | The system shall validate that a continuation matches the original job settings. |
| SRS-F-009 | The system shall generate a recovery report after restart. |
| SRS-F-010 | The system shall generate a partial continuation job with the original coordinate system and configured overlap. |
| SRS-F-011 | The system shall require operator approval in assisted mode. |
| SRS-F-012 | The system shall log every recovery decision and operator override. |
| SRS-F-013 | The system shall refuse certified recovery when the adapter cannot establish sufficient confidence. |

## External interface requirements

The system shall support modular adapters for hot folders, print queues, RIP logs, vendor-supported interfaces and local configuration files. The user interface shall show active jobs, interrupted jobs, confidence status, candidate resume point and warnings. The system shall export a human-readable recovery report and a machine-readable event file.

## Error handling requirements

If the source job is missing, the system shall recommend restart or restoration rather than generate a continuation. If critical settings differ, the system shall block automatic continuation. If the printer status is unavailable, the system shall downgrade confidence and use assisted mode. If checkpoint persistence fails, the system shall alert the operator and mark subsequent state as untrusted.
