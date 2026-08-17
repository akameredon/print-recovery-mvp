from pathlib import Path

from readiness_summary import summarize_readiness


def sample(
    readiness="blocked",
    blockers=None,
    warnings=None,
    integrity="missing",
    checkpoint=None,
    interruption=None,
):
    return {
        "job_id": "day60-test",
        "readiness": readiness,
        "source_integrity": {"status": integrity},
        "checkpoint_confidence": checkpoint,
        "interruption": interruption,
        "recovery_safety": {
            "blockers": blockers or [],
            "warnings": warnings or [],
            "safe_to_generate": not blockers,
        },
    }


blocked = summarize_readiness(
    sample(blockers=[{"code": "SOURCE_NOT_VERIFIED", "message": "Verify source"}])
)
assert blocked["blockers"][0]["code"] == "SOURCE_NOT_VERIFIED"
assert blocked["safe_to_generate"] is False
assert blocked["operator_confirmation_required"] is True
assert any("Resolve" in action for action in blocked["next_actions"])

review = summarize_readiness(
    sample(
        readiness="review_required",
        blockers=[],
        warnings=[{"code": "LOW_CONFIDENCE", "message": "Use a test"}],
        integrity="verified",
        checkpoint={"score": 0.7},
        interruption={"to_status": "INTERRUPTED"},
    )
)
assert review["warnings"][0]["code"] == "LOW_CONFIDENCE"
assert any("registration test" in action for action in review["next_actions"])

ready = summarize_readiness(
    sample(
        readiness="ready_for_operator_review",
        integrity="verified",
        checkpoint={"score": 1.0},
        interruption={"to_status": "INTERRUPTED"},
    )
)
assert ready["safe_to_generate"] is True
assert any("explicit operator approval" in action for action in ready["next_actions"])

template = Path("templates/index.html").read_text()
assert "/api/jobs/'+id+'/readiness-summary" in template
assert "loadReadiness" in template
assert "readiness-panel" in template
print({"status": "passed", "states": ["blocked", "review_required", "ready_for_operator_review"]})
