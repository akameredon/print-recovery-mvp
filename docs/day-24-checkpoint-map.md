# Day 24 — Visual checkpoint map

Each job card now includes a **Show checkpoint map** control. It loads the job detail record and renders checkpoint Y-coordinates along an accessible inline SVG axis. Physical confirmations use a green marker; other recorded confidence levels use the standard blue marker.

The map is a visual aid only. It does not claim that the printer physically stopped at every displayed coordinate.

Verification: `python3 test_dashboard_checkpoint_map.py` passed, confirming the rendered control, SVG function, checkpoint coordinate and job-detail data.
