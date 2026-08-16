"""لایه‌ی سرویس پنل ادمین — بخش ۵ پلن معماری. هر اقدام نوشتنی این ماژول
باید همراه با یک سطر در admin_audit_log باشه (log_action)."""

from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.core.slug import slugify_ascii
from app.models.admin_audit_log import AdminAuditLog
from app.models.base import utcnow
from app.models.category import Category
from app.models.event import Event
from app.models.review import EventReview
from app.models.user import User, UserStatus
from app.search.indexer import remove_event


class AdminServiceError(ValueError):
    pass


def log_action(
    db: Session,
    admin_user_id: int,
    action: str,
    target_type: str,
    target_id: int,
    reason: str | None = None,
) -> AdminAuditLog:
    entry = AdminAuditLog(
        admin_user_id=admin_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
    )
    db.add(entry)
    db.commit()
    return entry


def list_all_events(db: Session, status: str | None = None) -> list[Event]:
    """برخلاف event_service.event_query که فقط PUBLISHED+PUBLIC رو نشون
    می‌ده، ادمین باید همه‌چیز رو ببینه — شامل DRAFT/CANCELLED/PRIVATE (ولی نه
    رویدادهای soft-delete شده؛ اون‌ها فقط از طریق لاگ اقدامات قابل ردیابی‌ان)."""
    query = (
        db.query(Event)
        .filter(Event.deleted_at.is_(None))
        .options(selectinload(Event.organizer), selectinload(Event.category))
        .order_by(Event.created_at.desc())
    )
    if status is not None:
        query = query.filter(Event.status == status)
    return query.all()


def soft_delete_event(db: Session, event: Event) -> None:
    """تصمیم صریح کاربر: «حذف کامل» نباید واقعاً ردیف رو از DB پاک کنه —
    فقط باید از همه‌جای عمومی (event_query) و لیست ادمین ناپدید بشه، در حالی
    که خود رکورد و همه‌ی داده‌های مرتبطش (سفارش/ثبت‌نام/...) دست‌نخورده
    می‌مونه، هم برای امکان بازیابی دستی هم چون admin_audit_log (که همین
    الان هم برای این اکشن نوشته می‌شه) به target_id همین رویداد اشاره
    می‌کنه — اگه رکورد واقعاً پاک بشه، اون لاگ بی‌معنی می‌شه."""
    event.deleted_at = utcnow()
    remove_event(event.id)
    db.commit()


def set_event_featured(db: Session, event: Event, is_featured: bool) -> Event:
    event.is_featured = is_featured
    db.commit()
    db.refresh(event)
    return event


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def set_user_suspended(db: Session, user: User, suspended: bool) -> User:
    user.status = UserStatus.SUSPENDED if suspended else UserStatus.ACTIVE
    db.commit()
    db.refresh(user)
    return user


def create_category(db: Session, name: str, parent_id: int | None) -> Category:
    if parent_id is not None and db.get(Category, parent_id) is None:
        raise AdminServiceError("دسته‌ی والد یافت نشد")
    category = Category(name=name, slug=slugify_ascii(name, fallback_prefix="category"), parent_id=parent_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category: Category, name: str, parent_id: int | None) -> Category:
    if parent_id is not None and db.get(Category, parent_id) is None:
        raise AdminServiceError("دسته‌ی والد یافت نشد")
    category.name = name
    category.parent_id = parent_id
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    if category.children:
        raise AdminServiceError("این دسته زیردسته دارد؛ اول زیردسته‌ها را حذف/جابه‌جا کنید")
    if db.query(Event).filter(Event.category_id == category.id).first() is not None:
        raise AdminServiceError("رویدادی به این دسته وصل است؛ ابتدا دسته‌بندی آن رویدادها را تغییر دهید")
    db.delete(category)
    db.commit()


def list_audit_log(db: Session, limit: int = 100) -> list[AdminAuditLog]:
    return db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(limit).all()


def list_all_reviews(db: Session, limit: int = 100) -> list[EventReview]:
    """برخلاف review_service.list_event_reviews (فقط PUBLISHED، برای یک
    رویداد خاص)، ادمین باید همه‌چیز رو ببینه — شامل نظرهای hidden، از همه‌ی
    رویدادها — تا بتونه تصمیم بگیره چی رو hide/unhide کنه."""
    return db.query(EventReview).order_by(EventReview.created_at.desc()).limit(limit).all()
