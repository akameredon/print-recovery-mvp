# Day 30 — Operator usability review and paper workflow

## Review scope

Day 30 used an internal heuristic review of the MVP dashboard against the paper workflow an operator follows after a power outage or protection trip. This was a software review, not a field study with Nigerian print-shop operators; external operator validation remains a future requirement.

The review identified three usability risks: the recovery sequence was not visible as one checklist, the dashboard did not offer a print-friendly handoff for a shop floor, and asynchronous results could be difficult to locate after a button action. The dashboard changes address these risks with a six-step paper workflow, a Print checklist action, clear numbered steps and existing live output regions.

## Paper workflow

The checklist guides the operator through **Stabilize**, **Identify**, **Verify**, **Choose**, **Approve** and **Validate**. It explicitly preserves the assisted-recovery rule: the operator must review evidence, choose Continue/Test first/Restart and record approval or rejection before proceeding.

The print stylesheet hides interactive controls and runtime job panels while preserving the workflow card, allowing the checklist to be printed as a shop-floor reference. This is a convenience aid, not a substitute for machine-specific operating procedures or electrical safety training.

## Verification

```bash
python3 test_usability_workflow.py
```

The focused test verified the six workflow steps, main landmark, print action and print-media CSS. The complete executable regression suite passed after the changes.
