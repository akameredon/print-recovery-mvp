# Day 28 — Recovery action cards

## Purpose

Day 28 makes the recovery recommendation directly understandable to an operator by presenting three action cards on each dashboard job: **Continue**, **Test first** and **Restart**.

The cards are informational. When the operator requests a recommendation, the dashboard loads `/api/jobs/<job_id>/recommendation` and highlights only the action returned by the recovery logic. The three meanings are:

| Action | Meaning |
|---|---|
| `CONTINUE` | Use the proposed continuation after the required operator review. |
| `TEST_FIRST` | Print a registration test before attempting the continuation. |
| `RESTART` | Restart the job when recovery evidence is insufficient or unsafe. |

The cards do not bypass operator approval and do not send a print command. They make the existing assisted-recovery recommendation visible without changing its safety semantics.

## Verification

```bash
python3 test_action_cards.py
```

The focused test verifies all three cards, the recommendation-to-card mapping contract and the rendered dashboard controls. The complete executable regression suite passed after the feature was implemented.
