from coordinate_conversion import media_mm_to_pixel, pixel_to_media_mm

assert media_mm_to_pixel(0, 200, 100) == 0
assert media_mm_to_pixel(50, 200, 100) == 25
assert media_mm_to_pixel(100, 200, 100) == 50
assert media_mm_to_pixel(200, 200, 100) == 100
assert media_mm_to_pixel(12.5, 200, 100) == 6
assert media_mm_to_pixel(250, 200, 100) == 100
assert media_mm_to_pixel(250, 200, 100, clamp=False) == 125
assert pixel_to_media_mm(25, 100, 200) == 50.0
assert pixel_to_media_mm(100, 100, 200) == 200.0

for bad in (
    lambda: media_mm_to_pixel(-1, 200, 100),
    lambda: media_mm_to_pixel(1, 0, 100),
    lambda: media_mm_to_pixel(1, 200, 0),
    lambda: pixel_to_media_mm(-1, 100, 200),
    lambda: pixel_to_media_mm(101, 100, 200),
    lambda: pixel_to_media_mm(1, 0, 200),
):
    try:
        bad()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid coordinate input was accepted")

print({"status": "passed", "proportional_mapping": True, "invalid_inputs_rejected": True})
