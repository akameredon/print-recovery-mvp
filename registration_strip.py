from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def generate_registration_strip(
    source_path: Path,
    output_path: Path,
    *,
    selected_y_mm: float,
    media_length_mm: float,
    strip_height_mm: float,
) -> dict[str, Any]:
    if selected_y_mm < 0:
        raise ValueError("selected_y_mm must be non-negative")
    if media_length_mm <= 0:
        raise ValueError("media_length_mm must be positive")
    if strip_height_mm <= 0:
        raise ValueError("strip_height_mm must be positive")
    with Image.open(source_path) as source:
        if source.width <= 0 or source.height <= 0:
            raise ValueError("Image has no usable dimensions")
        selected_y_mm = min(selected_y_mm, media_length_mm)
        center_px = int(selected_y_mm / media_length_mm * source.height)
        half_height_px = max(1, int(strip_height_mm / media_length_mm * source.height / 2))
        crop_top = max(0, center_px - half_height_px)
        crop_bottom = min(source.height, center_px + half_height_px)
        crop = source.convert("RGB").crop((0, crop_top, source.width, crop_bottom))
        header_height = max(36, min(72, source.width // 8))
        canvas = Image.new("RGB", (crop.width, crop.height + header_height), "white")
        canvas.paste(crop, (0, header_height))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle(
            (0, header_height, crop.width - 1, canvas.height - 1), outline=(190, 35, 35), width=3
        )
        seam_y = header_height + center_px - crop_top
        draw.line((0, seam_y, crop.width - 1, seam_y), fill=(190, 35, 35), width=3)
        marker_x = crop.width // 2
        draw.line(
            (
                marker_x,
                max(header_height, seam_y - 14),
                marker_x,
                min(canvas.height - 1, seam_y + 14),
            ),
            fill=(20, 80, 160),
            width=3,
        )
        draw.text((8, 8), f"REGISTRATION STRIP · {selected_y_mm:.1f} mm", fill=(24, 33, 43))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, format="PNG")
        return {
            "width_px": canvas.width,
            "height_px": canvas.height,
            "crop_top_y_mm": round(crop_top / source.height * media_length_mm, 2),
            "crop_bottom_y_mm": round(crop_bottom / source.height * media_length_mm, 2),
            "selected_y_mm": round(selected_y_mm, 2),
            "strip_height_mm": round(strip_height_mm, 2),
        }
