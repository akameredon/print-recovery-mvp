# Day 25 — Evidence-confidence badges

Each job card now displays four evidence-confidence badges: **Prepared**, **Transmitted**, **Acknowledged** and **Physically confirmed**. The refresh control loads the job’s checkpoints and highlights levels that have actually been recorded.

A highlighted badge means that the corresponding software evidence exists; it does not upgrade weaker evidence to physical confirmation. This distinction preserves the project’s evidence hierarchy.

Verification: `python3 test_dashboard_confidence.py` passed, confirming all four confidence levels, the rendered badges and the dynamic refresh function.
