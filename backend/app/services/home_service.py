"""بخش‌های الگوریتمی صفحه‌ی اصلی — بخش ۱۰ پلن معماری، هرکدوم در Redis کش
می‌شن (TTL ۵ دقیقه) تا هر لود صفحه‌ی اصلی چند کوئری سنگین اجرا نکنه.

دو بخش از پلن اصلی (برترین وبینارها بر اساس امتیاز، محبوب‌ترین ویدیوهای
ضبط‌شده) عمداً اینجا نیستن چون داده‌ی واقعی پشتشون نیست: سیستم امتیازدهی
فاز ۷ هنوز پیاده نشده (rating_avg همه صفره) و مفهوم «ضبط رویداد گذشته»
(recording_url) اصلاً تو مدل داده نیست (promo_video_url چیز دیگه‌ایه —
کلیپ تبلیغاتی قبل از رویداد). ساختن این بخش‌ها با داده‌ی فیک/خالی به‌جای
واقعی، بدتر از نبودشونه.
"""

from __future__ import annotations

from redis import Redis
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus, EventVisibility
from app.models.favorite import OrganizerFollow
from app.models.user import User
from app.schemas.home import HomeSectionsOut, OrganizerSummaryOut
from app.schemas.instructor import InstructorOut
from app.services import instructor_service
from app.services.event_service import event_query, to_list_item_out

CACHE_KEY = "home:sections"
CACHE_TTL_SECONDS = 300
SECTION_LIMIT = 6


def _published_public_query(db: Session):
    return event_query(db).filter(
        Event.status == EventStatus.PUBLISHED, Event.visibility == EventVisibility.PUBLIC
    )


def _popular_events(db: Session) -> list:
    events = _published_public_query(db).order_by(Event.view_count.desc()).limit(SECTION_LIMIT).all()
    return [to_list_item_out(e) for e in events]


def _latest_events(db: Session) -> list:
    events = (
        _published_public_query(db).order_by(Event.published_at.desc()).limit(SECTION_LIMIT).all()
    )
    return [to_list_item_out(e) for e in events]


def _featured_events(db: Session) -> list:
    """رویداد «ویژه» باید واقعاً از بقیه متمایز باشه، نه صرفاً جدیدترین‌ها
    (که خودش بخش «آخرین وبینارها»ست) — طبق بازخورد کاربر. تا وقتی پنل ادمین
    (فاز ۵) امکان `is_featured` دستی رو نداره، fallback بر اساس محبوبیتِ
    واقعیِ برگزارکننده (تعداد دنبال‌کننده‌اش) انتخاب می‌شه، نه تاریخ انتشار.
    اگه هیچ برگزارکننده‌ی دنبال‌شده‌ای نباشه، بخش می‌تونه کمتر از SECTION_LIMIT
    (حتی خالی) بمونه — نشون‌دادن رویداد تصادفی به‌جای «ویژه» بدتر از خالی‌بودنه.
    """
    featured = (
        _published_public_query(db)
        .filter(Event.is_featured.is_(True))
        .order_by(Event.published_at.desc())
        .limit(SECTION_LIMIT)
        .all()
    )
    if len(featured) < SECTION_LIMIT:
        existing_ids = {e.id for e in featured}
        popular_organizer_ids = [
            organizer_id
            for organizer_id, in db.query(OrganizerFollow.organizer_id)
            .group_by(OrganizerFollow.organizer_id)
            .order_by(func.count(OrganizerFollow.follower_user_id).desc())
            .all()
        ]
        for organizer_id in popular_organizer_ids:
            if len(featured) >= SECTION_LIMIT:
                break
            candidates = (
                _published_public_query(db)
                .filter(Event.organizer_id == organizer_id)
                .order_by(Event.published_at.desc())
                .all()
            )
            for candidate in candidates:
                if len(featured) >= SECTION_LIMIT:
                    break
                if candidate.id not in existing_ids:
                    featured.append(candidate)
                    existing_ids.add(candidate.id)
    return [to_list_item_out(e) for e in featured]


def _popular_organizers(db: Session) -> list[OrganizerSummaryOut]:
    rows = (
        db.query(User, func.count(OrganizerFollow.follower_user_id))
        .join(OrganizerFollow, OrganizerFollow.organizer_id == User.id)
        .group_by(User.id)
        .order_by(func.count(OrganizerFollow.follower_user_id).desc())
        .limit(SECTION_LIMIT)
        .all()
    )
    return [
        OrganizerSummaryOut(id=user.id, name=user.full_name or "", follower_count=count)
        for user, count in rows
    ]


def _popular_instructors(db: Session) -> list[InstructorOut]:
    rows = instructor_service.list_popular_instructors(db, limit=SECTION_LIMIT)
    return [
        InstructorOut(id=i.id, name=i.name, bio=i.bio, avatar_url=i.avatar_url, follower_count=c)
        for i, c in rows
    ]


def get_home_sections(db: Session, redis_client: Redis) -> HomeSectionsOut:
    cached = redis_client.get(CACHE_KEY)
    if cached:
        return HomeSectionsOut.model_validate_json(cached)

    sections = HomeSectionsOut(
        popular_events=_popular_events(db),
        latest_events=_latest_events(db),
        featured_events=_featured_events(db),
        popular_instructors=_popular_instructors(db),
        popular_organizers=_popular_organizers(db),
    )
    redis_client.set(CACHE_KEY, sections.model_dump_json(), ex=CACHE_TTL_SECONDS)
    return sections
