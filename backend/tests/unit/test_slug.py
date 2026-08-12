from app.core.slug import generate_numeric_code, slugify_ascii


def test_slugify_ascii_from_latin_title():
    assert slugify_ascii("AI Workshop 2026") == "ai-workshop-2026"


def test_slugify_ascii_lowercases_and_strips_symbols():
    assert slugify_ascii("Hello, World!!!") == "hello-world"


def test_slugify_ascii_falls_back_for_pure_persian_title():
    slug = slugify_ascii("وبینار هوش مصنوعی", fallback_prefix="event")
    assert slug.startswith("event-")
    assert len(slug) > len("event-")


def test_slugify_ascii_fallback_is_random_each_time():
    a = slugify_ascii("رویداد فارسی")
    b = slugify_ascii("رویداد فارسی")
    assert a != b


def test_generate_numeric_code_length_and_digits():
    code = generate_numeric_code(6)
    assert len(code) == 6
    assert code.isdigit()


def test_generate_numeric_code_varies():
    codes = {generate_numeric_code(6) for _ in range(20)}
    assert len(codes) > 1
