# Day 66 — Configurable Printer Profiles

**Status:** Implemented and verified  
**Roadmap day:** 66  
**Scope:** Durable configuration records for multiple printer/RIP workflows

## Delivered

Day 66 adds a durable `printer_profiles` table through schema migration 9. A profile stores the manufacturer, exact printer model, RIP name and version, connection mode, job input path, output or hot-folder path, observable signal families, recovery mode, physical-validation requirement, lifecycle status and timestamps.

The API supports listing, creating, reading, updating and retiring profiles through `/api/printer-profiles`. Profile names are unique, retired profiles are hidden from the active list, and all records default to the MVP’s explicit `assisted_only` recovery mode. Automatic recovery mode is rejected rather than silently accepted.

The dashboard now provides a profile editor and an inventory of stored profiles. This allows a shop to keep separate Mimaki, Roland or other printer/RIP configurations without pretending that a stored profile grants hardware control or proves universal compatibility.

| Capability | Day 66 status |
|---|---|
| Store multiple printer profiles | Implemented |
| Store printer/RIP identity and versions | Implemented |
| Store input/output or hot-folder paths | Implemented |
| Store observable signal families | Implemented |
| Enforce assisted-only recovery mode | Implemented |
| Update and retire profiles | Implemented |
| Automatic printer control | Not implemented |
| Universal RIP compatibility | Not certified |

## Security and safety boundary

Profile configuration is deliberately separate from printer control. The profile API validates required contract fields and rejects unsafe recovery modes, but it does not connect to a printer, execute a hot-folder command or certify a physical position. Technician-only configuration permissions remain a later roadmap item.

## Verification evidence

The focused `test_printer_profiles.py` test passed creation of multiple profiles, manufacturer/model variation, duplicate-name rejection, unsafe-mode rejection, update, retirement and dashboard rendering. Migration and diagnostics tests passed with schema versions 1 through 9.

The complete non-restart regression suite passed with Black, Ruff and Python compilation. The checkpoint durability test was run separately using its intended process-restart lifecycle and passed with the checkpoint and event preserved. Existing recovery, evidence, authentication, dashboard, observer, trace and usability tests remained passing.
