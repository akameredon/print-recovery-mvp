# Day 22 — Job search by metadata and date

## Purpose

Day 22 adds search across the job fields operators use when locating a previous print: file name, job ID, printer model and RIP name. Date bounds can be combined with the existing status filter and free-text search.

## Search endpoint

```text
GET /api/jobs?q=Mimaki
GET /api/jobs?filter=interrupted&q=banner
GET /api/jobs?date_from=2026-01-01&date_to=2026-01-31
```

The dashboard exposes the same controls at `/` with a free-text field and Created from/Created to date fields. Search is case-insensitive through SQLite’s text matching behavior for the local prototype. Date values must use `YYYY-MM-DD` and are applied to the job creation date inclusively.

The JSON response echoes the selected `filter`, `q`, `date_from` and `date_to` values, then returns the matching count and job records. Search matches `id`, `file_name`, `printer_model` and `rip_name`. Invalid date formats and invalid status-filter values return `INVALID_JOB_QUERY` with HTTP 400. A valid range with no matches returns an empty result rather than an error.

## Verification

The focused test covers file-name, printer-model, job-ID and date matches; combined status/search/date queries; filtered dashboard HTML; invalid dates; and valid empty ranges:

```bash
python3 test_job_search.py
```

The search feature locates recorded software evidence only. It does not infer physical printer position or establish recovery compatibility for a printer/RIP combination.
