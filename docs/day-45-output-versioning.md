# Day 45 — Continuation output naming and versioning

## Purpose

Day 45 makes every generated continuation output traceable to its source job and recovery selection. The filename now contains the continuation version, job identifier, shortened source hash, selected coordinate and overlap.

A generated file follows this pattern:

```text
continuation-v001_<job-id>_<source-hash>_from-90.0mm_overlap-5.0mm.png
```

Versions are allocated from the number of previously recorded generated-continuation decisions for the job. Existing files are also checked before writing, so a prior output is not overwritten. The `CONTINUATION_GENERATED` event and API response include the filename, version, full source hash, selected coordinate and overlap.

This naming convention helps an operator or technician connect a continuation image to the original job manifest and the recovery decision that produced it. It does not change the assisted-recovery requirement or certify physical alignment.

## Verification

```bash
python3 test_output_versioning.py
```

The focused test verifies deterministic naming, invalid version rejection, unique version 1 and version 2 outputs, source-hash inclusion and persisted event metadata. The complete non-destructive regression suite, Black and Ruff checks pass.
