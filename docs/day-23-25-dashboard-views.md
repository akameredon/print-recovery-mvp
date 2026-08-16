# Days 23–25 — Dashboard recovery evidence views

## Day 23 — Job-detail timeline view

Each job card now includes a **Show evidence timeline** control. It loads the existing chronological `/api/jobs/<job_id>/timeline` response and renders timestamp, evidence kind, event name and details in order. The view is read-only and does not create or alter recovery evidence.

## Day 24 — Visual checkpoint map

Each job card now includes a **Show checkpoint map** control. It loads the job detail record and renders checkpoint Y-coordinates along an accessible inline SVG axis. Physical confirmations use a green marker; other recorded confidence levels use the standard blue marker. The map is a visual aid and does not claim that a printer physically stopped at every displayed coordinate.

## Day 25 — Evidence-confidence badges

Each job card now displays four evidence-confidence badges: **Prepared**, **Transmitted**, **Acknowledged** and **Physically confirmed**. The refresh control loads the job’s checkpoints and highlights levels that have actually been recorded. A highlighted badge means the corresponding software evidence exists; it does not upgrade weaker evidence to physical confirmation.

## Verification

The focused dashboard tests passed for the three sequential improvements:

```bash
python3 test_dashboard_timeline.py
python3 test_dashboard_checkpoint_map.py
python3 test_dashboard_confidence.py
```

The Day 23, Day 24 and Day 25 changes were pushed in separate commits. The tests verify the rendered controls, associated JavaScript functions, timeline availability, checkpoint coordinates and all four confidence levels.
