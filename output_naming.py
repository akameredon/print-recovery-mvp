from __future__ import annotations


def continuation_output_name(
    job_id: str,
    source_hash: str,
    version: int,
    selected_y_mm: float,
    overlap_mm: float,
) -> str:
    """Build a filesystem-safe, traceable continuation filename."""
    if version < 1:
        raise ValueError("version must be positive")
    if selected_y_mm < 0 or overlap_mm < 0:
        raise ValueError("selected_y_mm and overlap_mm must be non-negative")
    source_token = "".join(character for character in str(source_hash) if character.isalnum())[:12]
    if not source_token:
        raise ValueError("source_hash must contain an alphanumeric token")
    return (
        f"continuation-v{version:03d}_{job_id}_{source_token}"
        f"_from-{selected_y_mm:.1f}mm_overlap-{overlap_mm:.1f}mm.png"
    )
