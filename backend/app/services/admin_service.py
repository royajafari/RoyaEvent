"""لایه‌ی سرویس پنل ادمین — بخش ۵ پلن معماری. هر اقدام نوشتنی این ماژول
باید همراه با یک سطر در admin_audit_log باشه (log_action)."""

from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.core.slug import slugify_ascii
from app.models.admin_audit_log import AdminAuditLog
from app.models.category import Category
from app.models.event import Event
from app.models.favorite import Favorite
from app.models.order import Order, OrderItem, Payment, Registration
from app.models.ticket import DiscountCode, TicketType
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
    می‌ده، ادمین باید همه‌چیز رو ببینه — شامل DRAFT/CANCELLED/PRIVATE."""
    query = (
        db.query(Event)
        .options(selectinload(Event.organizer), selectinload(Event.category))
        .order_by(Event.created_at.desc())
    )
    if status is not None:
        query = query.filter(Event.status == status)
    return query.all()


def delete_event_completely(db: Session, event: Event) -> None:
    """حذف کامل و برگشت‌ناپذیر — نه فقط لغو (که organizer خودش هم می‌تونه).
    چون چند جدول (ثبت‌نام/سفارش/بلیط/تخفیف) بدون cascade در سطح DB به
    events وصل‌ان، ترتیب حذف صریح رعایت می‌شه تا رکورد یتیم نمونه."""
    order_ids = [row[0] for row in db.query(Order.id).filter(Order.event_id == event.id).all()]

    db.query(Registration).filter(Registration.event_id == event.id).delete(synchronize_session=False)
    if order_ids:
        db.query(Payment).filter(Payment.order_id.in_(order_ids)).delete(synchronize_session=False)
        db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
        db.query(Order).filter(Order.id.in_(order_ids)).delete(synchronize_session=False)
    db.query(Favorite).filter(Favorite.event_id == event.id).delete(synchronize_session=False)
    db.query(TicketType).filter(TicketType.event_id == event.id).delete(synchronize_session=False)
    db.query(DiscountCode).filter(DiscountCode.event_id == event.id).delete(synchronize_session=False)

    remove_event(event.id)
    db.delete(event)  # sessions (delete-orphan) و ردیف‌های event_tags/event_instructors خودکار پاک می‌شن
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
