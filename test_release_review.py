from pathlib import Path

from release_review import run_release_review

report = run_release_review(Path(__file__).resolve().parent)
assert report["status"] == "ready_for_signoff", report
assert all(report["checks"].values())
assert "penetration test" in report["limitations"]
print({"status": "passed", "release_review": True, "all_checks": True})
