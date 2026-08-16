# Day 43 — Media-length to pixel-coordinate conversion tests

## Purpose

Day 43 centralizes the conversion between physical media coordinates in millimetres and source-image pixel positions. The shared helper is now used by both continuation preview rendering and continuation-image generation, reducing the risk that the two workflows interpret the same physical coordinate differently.

The conversion uses proportional mapping:

```text
pixel = floor(coordinate_mm / media_length_mm × pixel_length)
```

Coordinates are validated as non-negative, media length and pixel length must be positive, and normal coordinate conversion clamps to the image bounds. Distance conversion can disable clamping so overlap values can be bounded by the caller. A reverse conversion helper is included for auditable region metadata.

This conversion validates coordinate arithmetic only. It does not establish that a physical printer has reached the same position, and assisted-recovery operator confirmation remains required.

## Verification

```bash
python3 test_coordinate_conversion.py
```

The focused test covers proportional mapping, fractional flooring, image boundaries, reverse conversion and invalid inputs. The continuation-preview and per-job-overlap tests also pass, confirming that the shared helper is used in the recovery workflow. The complete non-destructive regression suite, Black and Ruff checks pass.
