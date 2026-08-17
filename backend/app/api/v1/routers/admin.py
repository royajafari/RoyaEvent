from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.core.rate_limit_middleware import limiter
from app.models.category import Category
from app.models.event import Event
from app.models.review import EventReview
from app.models.user import User
from app.schemas.admin import (
    AdminEventOut,
    AdminNotificationOut,
    AdminReviewOut,
    AdminUserOut,
    AuditLogEntryOut,
    CategoryIn,
    DeleteEventIn,
    FeatureToggleIn,
    HideReviewIn,
    SuspendUserIn,
)
from app.schemas.event import CategoryOut
from app.services import admin_service, review_service

router = APIRouter(prefix="/admin", tags=["admin"])

# طبق بخش ۶ architecture.md: سقف بالا برای ادمین، فقط برای جلوگیری از
# اسکریپت‌های رهاشده — هر اقدام مستقل از این، در admin_audit_log ثبت می‌شه.
_ADMIN_RATE_LIMIT = "300/minute"


def _to_admin_event_out(event: Event) -> AdminEventOut:
    return AdminEventOut(
        id=event.id,
        title=event.title,
        slug=event.slug,
        event_code=event.event_code,
        status=event.status.value,
        is_featured=event.is_featured,
        organizer_id=event.organizer_id,
        organizer_name=event.organizer_name,
        created_at=event.created_at,
    )


@router.get("/events", response_model=list[AdminEventOut])
@limiter.limit(_ADMIN_RATE_LIMIT)
def list_events(
    request: Request,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    events = admin_service.list_all_events(db, status=status_filter)
    return [_to_admin_event_out(e) for e in events]


@router.delete("/events/{event_id}")
@limiter.limit(_ADMIN_RATE_LIMIT)
def delete_event(
    request: Request,
    event_id: int,
    body: DeleteEventIn = DeleteEventIn(),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    admin_service.soft_delete_event(db, event)
    admin_service.log_action(db, admin.id, "delete_event", "event", event_id, body.reason)
    return {"success": True}


@router.patch("/events/{event_id}/feature", response_model=AdminEventOut)
@limiter.limit(_ADMIN_RATE_LIMIT)
def toggle_event_featured(
    request: Request,
    event_id: int,
    body: FeatureToggleIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "رویداد یافت نشد")
    event = admin_service.set_event_featured(db, event, body.is_featured)
    action = "feature_event" if body.is_featured else "unfeature_event"
    admin_service.log_action(db, admin.id, action, "event", event_id)
    return _to_admin_event_out(event)


@router.get("/users", response_model=list[AdminUserOut])
@limiter.limit(_ADMIN_RATE_LIMIT)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return admin_service.list_users(db)


@router.patch("/users/{user_id}/suspend", response_model=AdminUserOut)
@limiter.limit(_ADMIN_RATE_LIMIT)
def suspend_user(
    request: Request,
    user_id: int,
    body: SuspendUserIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "کاربر یافت نشد")
    if user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "امکان تعلیق حساب خودتان وجود ندارد")
    user = admin_service.set_user_suspended(db, user, body.suspended)
    action = "suspend_user" if body.suspended else "unsuspend_user"
    admin_service.log_action(db, admin.id, action, "user", user_id, body.reason)
    return user


@router.get("/categories", response_model=list[CategoryOut])
@limiter.limit(_ADMIN_RATE_LIMIT)
def list_categories(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return db.query(Category).order_by(Category.parent_id.is_(None).desc(), Category.name).all()


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(_ADMIN_RATE_LIMIT)
def create_category(
    request: Request,
    body: CategoryIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    try:
        category = admin_service.create_category(db, body.name, body.parent_id)
    except admin_service.AdminServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    admin_service.log_action(db, admin.id, "create_category", "category", category.id)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryOut)
@limiter.limit(_ADMIN_RATE_LIMIT)
def update_category(
    request: Request,
    category_id: int,
    body: CategoryIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "دسته‌بندی یافت نشد")
    try:
        category = admin_service.update_category(db, category, body.name, body.parent_id)
    except admin_service.AdminServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    admin_service.log_action(db, admin.id, "update_category", "category", category_id)
    return category


@router.delete("/categories/{category_id}")
@limiter.limit(_ADMIN_RATE_LIMIT)
def delete_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "دسته‌بندی یافت نشد")
    try:
        admin_service.delete_category(db, category)
    except admin_service.AdminServiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    admin_service.log_action(db, admin.id, "delete_category", "category", category_id)
    return {"success": True}


@router.get("/audit-log", response_model=list[AuditLogEntryOut])
@limiter.limit(_ADMIN_RATE_LIMIT)
def get_audit_log(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    entries = admin_service.list_audit_log(db)
    return [
        AuditLogEntryOut(
            id=e.id,
            admin_user_id=e.admin_user_id,
            admin_name=e.admin_user.full_name if e.admin_user else None,
            action=e.action,
            target_type=e.target_type,
            target_id=e.target_id,
            reason=e.reason,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.get("/notifications", response_model=list[AdminNotificationOut])
@limiter.limit(_ADMIN_RATE_LIMIT)
def list_notifications(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    notifications = admin_service.list_notifications(db)

    def _event_title(event_id: int | None) -> str | None:
        if event_id is None:
            return None
        event = db.get(Event, event_id)
        return event.title if event else None

    return [
        AdminNotificationOut(
            id=n.id,
            channel=n.channel.value,
            destination=n.destination,
            template_key=n.template_key.value,
            status=n.status.value,
            attempts=n.attempts,
            provider=n.provider,
            last_error=n.last_error,
            event_id=n.event_id,
            event_title=_event_title(n.event_id),
            created_at=n.created_at,
        )
        for n in notifications
    ]


def _to_admin_review_out(db: Session, review: EventReview) -> AdminReviewOut:
    event = db.get(Event, review.event_id)
    reviewer = db.get(User, review.user_id)
    return AdminReviewOut(
        id=review.id,
        event_id=review.event_id,
        event_title=event.title if event else "",
        user_id=review.user_id,
        user_name=reviewer.full_name if reviewer else None,
        overall_computed=review.overall_computed,
        comment_text=review.comment_text,
        status=review.status.value,
        hidden_reason=review.hidden_reason,
        created_at=review.created_at,
    )


@router.get("/reviews", response_model=list[AdminReviewOut])
@limiter.limit(_ADMIN_RATE_LIMIT)
def list_reviews(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    reviews = admin_service.list_all_reviews(db)
    return [_to_admin_review_out(db, r) for r in reviews]


@router.patch("/reviews/{review_id}/hide", response_model=AdminReviewOut)
@limiter.limit(_ADMIN_RATE_LIMIT)
def hide_review(
    request: Request,
    review_id: int,
    body: HideReviewIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    review = db.get(EventReview, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "نظر یافت نشد")
    review = review_service.set_review_hidden(db, review, hidden=body.hidden, reason=body.reason)
    action = "hide_review" if body.hidden else "unhide_review"
    admin_service.log_action(db, admin.id, action, "review", review_id, body.reason)
    return _to_admin_review_out(db, review)
