# Day 39 — Checkpoint confidence calculation rules

## Purpose

Day 39 adds transparent confidence scoring for checkpoint evidence. The score supports assisted recovery review; it is not a certification of exact physical printer position.

| Rule | Effect |
|---|---:|
| Prepared evidence | Base score 0.25 |
| Transmitted evidence | Base score 0.50 |
| Acknowledged evidence | Base score 0.75 |
| Physically confirmed evidence | Base score 0.95 |
| Both logical band and pass number present | +0.05 |
| Invalid or negative coordinate | −0.25 |
| Score at least 0.85 | High |
| Score from 0.60 through 0.84 | Medium |
| Score below 0.60 | Low |

The API returns the score, level and factor explanations when creating a checkpoint. The recovery-readiness response also includes the calculated result for the latest checkpoint. Existing evidence labels remain intact so the rule is additive and auditable.

## Limitations

A high score means that the available software evidence is stronger under these rules. It does not prove that a printer has physically completed the same amount of work, and operator confirmation remains mandatory.

## Verification

```bash
python3 test_checkpoint_confidence.py
```

The focused test covers all score bands, factor transparency, checkpoint API output and readiness output.
