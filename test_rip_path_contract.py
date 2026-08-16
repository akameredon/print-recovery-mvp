from rip_path_contract import validate_path_contract

valid_windows = validate_path_contract(
    {
        "connection_mode": "hot_folder",
        "job_input_path": r"C:\\Print\Input",
        "job_output_or_hotfolder": r"C:\\Print\Output",
    }
)
assert valid_windows["status"] == "ready_for_signoff"
assert valid_windows["errors"] == []

valid_linux = validate_path_contract(
    {
        "connection_mode": "watched_folder",
        "job_input_path": "/srv/print/input",
        "job_output_or_hotfolder": "/srv/print/output",
    }
)
assert valid_linux["status"] == "ready_for_signoff"

for field in ("job_input_path", "job_output_or_hotfolder"):
    invalid = validate_path_contract(
        {
            "connection_mode": "hot_folder",
            "job_input_path": r"C:\\Print\Input",
            "job_output_or_hotfolder": r"C:\\Print\Output",
            field: "TO_BE_CONFIRMED",
        }
    )
    assert invalid["status"] == "invalid"
    assert {item["code"] for item in invalid["errors"]} >= {"PATH_UNCONFIRMED"}
traversal = validate_path_contract(
    {
        "connection_mode": "hot_folder",
        "job_input_path": "/srv/print/../secrets",
        "job_output_or_hotfolder": "/srv/print/output",
    }
)
assert any(item["code"] == "PATH_TRAVERSAL" for item in traversal["errors"])
collision = validate_path_contract(
    {
        "connection_mode": "watched_folder",
        "job_input_path": r"C:\\Print\Folder",
        "job_output_or_hotfolder": r"c:\\print\folder",
    }
)
assert any(item["code"] == "PATH_COLLISION" for item in collision["errors"])
mode = validate_path_contract(
    {
        "connection_mode": "serial",
        "job_input_path": "/srv/input",
        "job_output_or_hotfolder": "/srv/output",
    }
)
assert any(item["code"] == "INVALID_CONNECTION_MODE" for item in mode["errors"])
print({"status": "passed", "windows": True, "linux": True, "unsafe_paths_blocked": True})
