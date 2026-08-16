# Day 23 — Job-detail timeline view

Each job card now includes a **Show evidence timeline** control. It loads the chronological `/api/jobs/<job_id>/timeline` response and renders timestamp, evidence kind, event name and details in order. The view is read-only and does not create or alter recovery evidence.

Verification: `python3 test_dashboard_timeline.py` passed, confirming the rendered control, timeline output target and existing timeline API.
