# Day 52 — RIP job input and output path contract

## Purpose

Day 52 defines the path contract needed before observing a real RIP workflow. The validator supports `hot_folder`, `watched_folder`, `manual_export` and `api` connection modes. It validates the job input path and output or hot-folder path without touching the filesystem or assuming that an unverified path exists.

| Check | Result |
|---|---|
| Placeholder path such as `TO_BE_CONFIRMED` | Invalid until the target shop confirms it |
| Relative or ambiguous path | Warning requiring review |
| `..` traversal component | Invalid |
| Same input and output path | Invalid collision |
| Unsupported connection mode | Invalid |
| Absolute Windows or Linux paths with distinct locations | Structurally ready for sign-off |

The path asset is intentionally platform-neutral: Windows drive paths and UNC paths are accepted alongside Linux absolute paths. The committed Mimaki/RasterLink6 target contract still contains placeholders because the actual shop’s RIP input, output or hot-folder locations have not been supplied. No physical integration is claimed.

## Verification

```bash
python3 test_rip_path_contract.py
```

The focused test covers Windows and Linux path forms, unresolved placeholders, traversal, input/output collisions and unsupported connection modes. The complete non-destructive regression suite, Black and Ruff checks pass.
