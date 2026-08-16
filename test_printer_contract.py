import json
from pathlib import Path

from printer_contract import validate_contract

contract_path = Path("docs/target-contracts/mimaki-jv150-rasterlink6.json")
contract = json.loads(contract_path.read_text(encoding="utf-8"))
result = validate_contract(contract)
assert result["status"] == "invalid"
assert {item["field"] for item in result["errors"]} >= {
    "rip_version",
    "connection_mode",
    "job_input_path",
    "job_output_or_hotfolder",
}
assert any(item["code"] == "SIGNOFF_REQUIRED" for item in result["warnings"])

signed_off = dict(contract)
signed_off.update(
    {
        "status": "signed_off",
        "rip_version": "RasterLink6-confirmed",
        "connection_mode": "hot_folder",
        "job_input_path": "operator-confirmed-input",
        "job_output_or_hotfolder": "operator-confirmed-hot-folder",
    }
)
ready = validate_contract(signed_off)
assert ready["status"] == "ready_for_signoff"
assert ready["errors"] == []
assert ready["warnings"] == []
unsafe = dict(signed_off, recovery_mode="automatic")
unsafe_result = validate_contract(unsafe)
assert unsafe_result["status"] == "invalid"
assert any(item["code"] == "UNSAFE_RECOVERY_MODE" for item in unsafe_result["errors"])
print({"status": "passed", "proposal_requires_signoff": True, "signed_contract_validated": True})
