import pytest

from app.services.video_service import MAX_UPLOAD_BYTES, InvalidVideoError, validate_video_file


def _mp4_bytes(extra: bytes = b"") -> bytes:
    # باکس ISO-BMFF: ۴ بایت اندازه + "ftyp" + brand مینیمال
    return b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + extra


def _webm_bytes(extra: bytes = b"") -> bytes:
    return b"\x1a\x45\xdf\xa3" + b"\x00" * 20 + extra


def test_valid_mp4_is_accepted():
    assert validate_video_file(_mp4_bytes()) == "video/mp4"


def test_valid_webm_is_accepted():
    assert validate_video_file(_webm_bytes()) == "video/webm"


def test_rejects_empty_file():
    with pytest.raises(InvalidVideoError):
        validate_video_file(b"")


def test_rejects_non_video_bytes():
    with pytest.raises(InvalidVideoError):
        validate_video_file(b"this is definitely not a video file, no magic bytes here")


def test_rejects_file_over_size_limit():
    raw = _mp4_bytes() + b"0" * (MAX_UPLOAD_BYTES + 1)
    with pytest.raises(InvalidVideoError):
        validate_video_file(raw)


def test_rejects_image_disguised_with_video_extension():
    jpeg_magic = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    with pytest.raises(InvalidVideoError):
        validate_video_file(jpeg_magic)
