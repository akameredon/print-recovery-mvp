from __future__ import annotations


def media_mm_to_pixel(
    coordinate_mm: float,
    media_length_mm: float,
    pixel_length: int,
    *,
    clamp: bool = True,
) -> int:
    """Convert a media coordinate or distance in millimetres to a pixel index."""
    coordinate = float(coordinate_mm)
    media_length = float(media_length_mm)
    pixels = int(pixel_length)
    if coordinate < 0:
        raise ValueError("coordinate_mm must be non-negative")
    if media_length <= 0:
        raise ValueError("media_length_mm must be positive")
    if pixels <= 0:
        raise ValueError("pixel_length must be positive")
    converted = int(coordinate / media_length * pixels)
    return max(0, min(pixels, converted)) if clamp else converted


def pixel_to_media_mm(pixel: int, pixel_length: int, media_length_mm: float) -> float:
    """Convert a pixel index back to millimetres for auditable region metadata."""
    pixel_index = int(pixel)
    pixels = int(pixel_length)
    media_length = float(media_length_mm)
    if pixel_index < 0 or pixel_index > pixels:
        raise ValueError("pixel must be within the image bounds")
    if pixels <= 0:
        raise ValueError("pixel_length must be positive")
    if media_length <= 0:
        raise ValueError("media_length_mm must be positive")
    return round(pixel_index / pixels * media_length, 6)
