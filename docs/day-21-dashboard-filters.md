# Day 21 — Dashboard job filters

## Purpose

Day 21 adds operator-facing job filters for the dashboard. The same filtering contract is available through the HTML dashboard and a JSON jobs-list endpoint, so a future dashboard client can use identical definitions.

## Filter endpoint

```text
GET /api/jobs?filter=all
GET /api/jobs?filter=active
GET /api/jobs?filter=interrupted
GET /api/jobs?filter=completed
```

The dashboard uses the equivalent browser URLs, such as `/?filter=interrupted`. The default is `all`.

| Filter | Included statuses |
|---|---|
| `all` | Every job. |
| `active` | `READY`, `PRINTING`, `RECOVERY_READY` and `RECOVERING`. |
| `interrupted` | `INTERRUPTED`. |
| `completed` | `COMPLETED`. |

The JSON response includes the selected filter, result count and job records. Unknown filters return `INVALID_JOB_FILTER` with HTTP 400. The dashboard presents the selected filter and matching count, and shows a clear empty-state message when no jobs match.

## Verification

The focused test creates active, interrupted and completed jobs, verifies each API category, checks that the dashboard HTML displays only the selected category and confirms invalid-filter handling:

```bash
python3 test_dashboard_filters.py
```

This is a status-based dashboard filter. It does not infer physical printer state or claim that an interrupted job is safe to resume.
