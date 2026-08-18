from pathlib import Path

pack = (Path(__file__).resolve().parent / "docs" / "day-91-to-98-beta-readiness.md").read_text(
    encoding="utf-8"
)
for marker in [
    "Day 91",
    "Day 92",
    "Day 93",
    "Day 94",
    "Day 95",
    "Day 96",
    "Day 97",
    "Day 98",
    "field evidence",
    "does not guarantee physical alignment",
    "Supported messaging",
    "Known limitations",
]:
    assert marker in pack, marker
assert "planned" in pack.lower()
assert "field-validated" in pack.lower()
print({"status": "passed", "days_91_98": True, "evidence_boundary": True})
