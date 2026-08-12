import io

import pytest
from PIL import Image

from app.services.image_service import (
    MAX_DIMENSION_PX,
    MAX_UPLOAD_BYTES,
    InvalidImageError,
    validate_and_reencode_image,
)


def _make_image_bytes(fmt: str, size: tuple[int, int] = (200, 100), mode: str = "RGB") -> bytes:
    image = Image.new(mode, size, color=(255, 0, 0) if mode == "RGB" else (255, 0, 0, 128))
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def test_valid_jpeg_is_reencoded_to_jpeg():
    raw = _make_image_bytes("JPEG")
    output = validate_and_reencode_image(raw)
    reencoded = Image.open(io.BytesIO(output))
    assert reencoded.format == "JPEG"
    assert reencoded.size == (200, 100)


def test_valid_png_with_transparency_is_flattened_to_jpeg():
    raw = _make_image_bytes("PNG", mode="RGBA")
    output = validate_and_reencode_image(raw)
    reencoded = Image.open(io.BytesIO(output))
    assert reencoded.format == "JPEG"
    assert reencoded.mode == "RGB"


def test_valid_webp_is_accepted():
    raw = _make_image_bytes("WEBP")
    output = validate_and_reencode_image(raw)
    reencoded = Image.open(io.BytesIO(output))
    assert reencoded.format == "JPEG"


def test_output_never_contains_original_bytes_verbatim():
    """اطمینان از این‌که فایل خروجی صرفاً re-encode شده، نه کپی بایت‌های خام
    (شبیه‌سازی این‌که هر payload الحاقی/steganography به فایل اصلی از بین می‌رود)."""
    raw = _make_image_bytes("PNG") + b"HIDDEN_MALICIOUS_PAYLOAD_TAIL_BYTES"
    output = validate_and_reencode_image(raw)
    assert b"HIDDEN_MALICIOUS_PAYLOAD_TAIL_BYTES" not in output
    # فایل خروجی باید یک JPEG کاملاً قابل دیکد باشد
    Image.open(io.BytesIO(output)).load()


def test_rejects_empty_file():
    with pytest.raises(InvalidImageError):
        validate_and_reencode_image(b"")


def test_rejects_non_image_bytes():
    with pytest.raises(InvalidImageError):
        validate_and_reencode_image(b"this is definitely not an image file")


def test_rejects_svg_disguised_as_image():
    svg_payload = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
    with pytest.raises(InvalidImageError):
        validate_and_reencode_image(svg_payload)


def test_rejects_file_over_size_limit():
    raw = _make_image_bytes("JPEG") + b"0" * (MAX_UPLOAD_BYTES + 1)
    with pytest.raises(InvalidImageError):
        validate_and_reencode_image(raw)


def test_rejects_oversized_dimensions():
    raw = _make_image_bytes("PNG", size=(MAX_DIMENSION_PX + 10, 10))
    with pytest.raises(InvalidImageError):
        validate_and_reencode_image(raw)
