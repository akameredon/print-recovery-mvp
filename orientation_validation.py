from __future__ import annotations

from math import isfinite
from typing import Any

ALLOWED_ORIENTATIONS = {"top-left", "top-right", "bottom-left", "bottom-right"}


def validate_orientation_origin(
    *,
    image_width_px: int,
    image_height_px: int,
    media_width_mm: float,
    media_length_mm: float,
    origin_x_mm: float,
    origin_y_mm: float,
    orientation: str,
    aspect_tolerance: float = 0.10,
) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []
    errors: list[str] = []
    normalized = str(orientation or "").strip().lower()
    values = {
        "image_width_px": image_width_px,
        "image_height_px": image_height_px,
        "media_width_mm": media_width_mm,
        "media_length_mm": media_length_mm,
        "origin_x_mm": origin_x_mm,
        "origin_y_mm": origin_y_mm,
    }
    if normalized not in ALLOWED_ORIENTATIONS:
        errors.append("orientation must be one of: " + ", ".join(sorted(ALLOWED_ORIENTATIONS)))
    if image_width_px <= 0 or image_height_px <= 0:
        errors.append("image dimensions must be positive")
    if media_width_mm <= 0 or media_length_mm <= 0:
        errors.append("media dimensions must be positive")
    if any(not isfinite(float(value)) for value in values.values()):
        errors.append("all dimensions and origins must be finite")
    if origin_x_mm < 0 or origin_y_mm < 0:
        warnings.append(
            {
                "code": "NEGATIVE_ORIGIN",
                "message": "Origin is outside the positive media coordinate space.",
            }
        )
    if origin_x_mm > media_width_mm or origin_y_mm > media_length_mm:
        warnings.append(
            {
                "code": "ORIGIN_OUTSIDE_MEDIA",
                "message": "Origin lies beyond the declared media dimensions.",
            }
        )
    if image_width_px > 0 and image_height_px > 0 and media_width_mm > 0 and media_length_mm > 0:
        image_ratio = image_width_px / image_height_px
        media_ratio = media_width_mm / media_length_mm
        deviation = abs(image_ratio - media_ratio) / media_ratio
        if deviation > aspect_tolerance:
            warnings.append(
                {
                    "code": "ASPECT_RATIO_MISMATCH",
                    "message": "Image aspect ratio differs materially from declared media ratio.",
                }
            )
    status = "invalid" if errors else ("warning" if warnings else "verified")
    return {
        "status": status,
        "orientation": normalized,
        "warnings": warnings,
        "errors": errors,
        "image": {"width_px": image_width_px, "height_px": image_height_px},
        "media": {"width_mm": media_width_mm, "length_mm": media_length_mm},
        "origin": {"x_mm": origin_x_mm, "y_mm": origin_y_mm},
    }
