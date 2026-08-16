# Day 51 — First printer/RIP target contract

## Purpose

Day 51 establishes the first exact integration target for the upcoming printer/RIP observation work: a **Mimaki JV150-series printer with RasterLink6**. The contract is stored as machine-readable JSON at `docs/target-contracts/mimaki-jv150-rasterlink6.json` and is deliberately marked `proposed_requires_operator_signoff`.

This distinction is important. The software can define the fields and acceptance gates, but it cannot claim that a real machine, firmware version, RasterLink6 version, hot-folder path or progress signal has been validated without access to that shop’s equipment and sample jobs.

| Contract area | Current state |
|---|---|
| Manufacturer and printer family | Proposed: Mimaki JV150-series |
| RIP | Proposed: RasterLink6; exact version still requires confirmation |
| Connection mode | Requires confirmation from the target shop |
| Input and output paths | Requires confirmation from the target workflow |
| Observable signals | Host job creation, transmission, checkpoints and interruption records are listed as candidate signals |
| Recovery mode | Assisted recovery only |
| Physical validation | Exact model, firmware, RIP version, paths, queue signals and controlled interruption results are required |

The validator in `printer_contract.py` rejects unresolved required fields and unsafe automatic-recovery modes. It distinguishes an incomplete proposal from a complete contract that has been populated and signed off.

## Verification

```bash
python3 test_printer_contract.py
```

The focused test confirms that the committed proposal requires sign-off, that a completed assisted-only contract passes structural validation, and that automatic recovery is rejected. The complete non-destructive regression suite, Black and Ruff checks pass.

The Day 51 software asset is therefore **verified as a contract-validation milestone**, while the physical printer/RIP contract remains explicitly **pending operator and equipment sign-off**.
