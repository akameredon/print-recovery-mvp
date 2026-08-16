# Day 27 — Operator approval dialog

## Purpose

Day 27 adds an operator-facing approval dialog to the dashboard. It lets the operator load the latest persisted recovery decision, inspect its review state and explicitly approve or reject it with a note.

The dialog uses the existing read-only review summary endpoint and the existing review command:

```text
GET  /api/jobs/<job_id>/review
POST /api/jobs/<job_id>/review
```

Approval and rejection remain explicit operator actions. Each submitted review updates the latest decision and creates a `RECOVERY_REVIEWED` audit event. The dialog never sends a print command and does not silently authorize continuation outside the existing assisted-recovery workflow.

Review notes use the existing 1,000-character validation limit. The visible panel includes the current review state, a note field, an approve action and a reject action.

## Verification

```bash
python3 test_operator_approval_dialog.py
```

The focused test verified the rendered dialog controls, continuation decision creation, approved review persistence and `RECOVERY_REVIEWED` audit-event creation. The complete executable regression suite also passed after the feature was implemented.
