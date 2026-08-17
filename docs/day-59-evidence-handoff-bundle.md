# Day 59 — Evidence review and operator handoff bundle

## Purpose

Day 59 adds a consolidated evidence handoff bundle for operator review. The endpoint is:

```text
GET /api/jobs/<job_id>/evidence-bundle
```

The default JSON response combines the canonical job manifest, recovery-report summary, checkpoints, event history and an explicit operator checklist. A Markdown handoff is available with `?format=md` for printing, saving or attaching to a job record.

| Bundle section | Handoff purpose |
|---|---|
| Manifest | Confirms source hash, printer/RIP metadata and media geometry |
| Recovery summary | Shows source-integrity state, latest coordinate and evidence counts |
| Checkpoints and events | Preserves chronological evidence for review |
| Operator checklist | Separates completed evidence checks from required human actions |
| Limitations | Prevents the bundle from being mistaken for physical-position certification |

The bundle always starts in `operator_review_required` status. Source integrity and checkpoint presence may be marked complete, but registration confirmation and operator approval remain incomplete until explicitly recorded through the existing assisted-recovery workflow.

## Verification

```bash
python3 test_evidence_bundle.py
```

The focused test verifies JSON and Markdown output, manifest integrity, checkpoint and event inclusion, checklist gates and invalid-format handling. The complete non-destructive regression suite, Black and Ruff checks pass.
