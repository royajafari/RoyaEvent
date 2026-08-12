"""بذرپاشی دسته‌بندی دوسطحی اولیه — بخش ۴ پلن معماری.

اجرا: python -m app.db.seed_categories
Idempotent است: اگر دسته‌ای با همان slug از قبل باشد، دوباره ساخته نمی‌شود.
"""

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.category import Category

CATEGORY_TREE: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "کسب‌وکار و کارآفرینی",
        "business",
        [
            ("استارتاپ و کارآفرینی", "startup"),
            ("بازاریابی دیجیتال", "digital-marketing"),
            ("فروش", "sales"),
            ("مدیریت", "management"),
            ("سرمایه‌گذاری", "investment"),
        ],
    ),
    (
        "فناوری اطلاعات",
        "technology",
        [
            ("هوش مصنوعی", "ai"),
            ("برنامه‌نویسی", "programming"),
            ("امنیت سایبری", "cybersecurity"),
            ("داده و تحلیل", "data-analytics"),
        ],
    ),
    (
        "توسعه فردی",
        "self-development",
        [
            ("رشد فردی", "personal-growth"),
            ("مهارت‌های نرم", "soft-skills"),
            ("زبان‌های خارجی", "languages"),
            ("مهاجرت", "immigration"),
        ],
    ),
    (
        "سلامت و پزشکی",
        "health",
        [
            ("پزشکی عمومی", "general-medicine"),
            ("روان‌شناسی", "psychology"),
            ("تغذیه", "nutrition"),
        ],
    ),
    (
        "مالی و اقتصاد",
        "finance",
        [
            ("بورس", "stock-market"),
            ("ارزهای دیجیتال", "crypto"),
            ("فارکس", "forex"),
            ("بیمه", "insurance"),
        ],
    ),
    (
        "هنر و فرهنگ",
        "art-culture",
        [
            ("سینما و تئاتر", "cinema-theater"),
            ("موسیقی", "music"),
            ("ادبیات", "literature"),
            ("طراحی", "design"),
        ],
    ),
    (
        "تحصیل و آموزش",
        "education",
        [
            ("کنکور و دانشگاه", "university-exams"),
            ("مهارت‌آموزی", "skill-training"),
            ("دوره‌های آنلاین", "online-courses"),
        ],
    ),
    (
        "فنی و مهندسی",
        "engineering",
        [
            ("عمران", "civil-engineering"),
            ("مکانیک", "mechanical-engineering"),
            ("برق و الکترونیک", "electrical-engineering"),
            ("صنایع", "industrial-engineering"),
        ],
    ),
    (
        "گردشگری و سرگرمی",
        "travel-entertainment",
        [
            ("سفر و گردشگری", "travel"),
            ("ورزش", "sports"),
            ("بازی و سرگرمی", "gaming"),
        ],
    ),
    (
        "مذهبی و اجتماعی",
        "religious-social",
        [
            ("مذهبی و مناسبتی", "religious-occasions"),
            ("خیریه", "charity"),
        ],
    ),
]


def seed_categories(db: Session) -> None:
    for parent_name, parent_slug, children in CATEGORY_TREE:
        parent = db.query(Category).filter_by(slug=parent_slug).first()
        if parent is None:
            parent = Category(name=parent_name, slug=parent_slug, parent_id=None)
            db.add(parent)
            db.flush()

        for child_name, child_slug in children:
            existing = db.query(Category).filter_by(slug=child_slug).first()
            if existing is None:
                db.add(Category(name=child_name, slug=child_slug, parent_id=parent.id))

    db.commit()


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed_categories(session)
        print("دسته‌بندی‌ها seed شدند.")
    finally:
        session.close()
