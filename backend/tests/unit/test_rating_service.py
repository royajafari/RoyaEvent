from app.services import rating_service


def test_rate_instructor_upsert(db_session, buyer, leaf_category, organizer):
    from datetime import datetime, timedelta

    from app.schemas.event import EventCreateIn, EventSessionIn
    from app.services import event_service

    event = event_service.create_event(
        db_session,
        organizer.id,
        EventCreateIn(
            title="کارگاه تست",
            description="توضیحات",
            category_id=leaf_category.id,
            format="online",
            online_platform_name="SkyRoom",
            instructor_names=["مدرس تست"],
            sessions=[EventSessionIn(starts_at=datetime.now() + timedelta(days=3), duration_minutes=60)],
        ),
    )
    instructor = event.instructors[0]

    rating_service.rate_instructor(db_session, buyer.id, instructor.id, 4)
    average, count = rating_service.instructor_rating_stats(db_session, instructor.id)
    assert average == 4.0
    assert count == 1

    rating_service.rate_instructor(db_session, buyer.id, instructor.id, 2)
    average, count = rating_service.instructor_rating_stats(db_session, instructor.id)
    assert average == 2.0
    assert count == 1
    assert rating_service.my_instructor_rating(db_session, buyer.id, instructor.id) == 2


def test_rate_organizer_upsert(db_session, buyer, organizer):
    rating_service.rate_organizer(db_session, buyer.id, organizer.id, 5)
    average, count = rating_service.organizer_rating_stats(db_session, organizer.id)
    assert average == 5.0
    assert count == 1
    assert rating_service.my_organizer_rating(db_session, buyer.id, organizer.id) == 5


def test_rate_platform_upsert(db_session, buyer):
    rating_service.rate_platform(db_session, buyer.id, 3)
    average, count = rating_service.platform_rating_stats(db_session)
    assert average == 3.0
    assert count == 1

    rating_service.rate_platform(db_session, buyer.id, 5)
    average, count = rating_service.platform_rating_stats(db_session)
    assert average == 5.0
    assert count == 1


def test_instructor_rating_stats_empty(db_session):
    average, count = rating_service.instructor_rating_stats(db_session, 999999)
    assert average == 0.0
    assert count == 0
