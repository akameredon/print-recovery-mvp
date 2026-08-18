# Target Contract — Suretec XP600 + Maintop

**Status:** Proposed, requires operator sign-off  
**Date added:** 2026-08-18

## Machine

| Field | Value |
|-------|-------|
| Manufacturer | Suretec |
| Model | XP600 (10FT) |
| Printhead | Epson XP600 (DX11) |
| Max print width | 1650 mm |
| Example media length | 10 feet (3048 mm) |
| Ink | Eco-solvent / Sublimation |
| Connection | USB 2.0 |
| RIP | Maintop (Full / DTP) |

## Contract file

Machine-readable contract:

`docs/target-contracts/suretec-xp600-maintop.json`

## Recovery mode

**Assisted only.**  
The software will capture job state, checkpoints and interruptions, then help the operator generate a continuation image for review. It will **not** send commands to the printer or RIP.

## What still needs confirmation on the real machine

1. Exact Maintop version number
2. Exact board / firmware (Hoson, KC, or other)
3. Whether Maintop exposes any readable job/queue status that can be observed
4. The normal job workflow (how files are sent from Maintop to the printer)
5. A controlled test with a known media length (e.g. 10 feet) so we can compare software checkpoints with physical position later

## Next steps

1. Install and run the Print Recovery software on the office PC
2. Create a test job using a real image and set media length to 3048 mm (10 feet)
3. Record checkpoints while a real job is running (or simulated)
4. Mark an interruption and generate a continuation
5. Later: capture real Maintop / USB behaviour so an observation adapter can be written

This contract replaces the earlier Mimaki proposal as the **primary** integration target for the current shop.
