from app.models.favorite import Favorite, InstructorFollow, OrganizerFollow
from app.models.instructor import Instructor
from app.services import social_service


def test_toggle_favorite_add_and_remove(db_session, buyer, published_event):
    added = social_service.toggle_favorite(db_session, buyer.id, published_event.id, add=True)
    assert added is True
    assert db_session.query(Favorite).filter_by(user_id=buyer.id, event_id=published_event.id).count() == 1

    removed = social_service.toggle_favorite(db_session, buyer.id, published_event.id, add=False)
    assert removed is False
    assert db_session.query(Favorite).filter_by(user_id=buyer.id, event_id=published_event.id).count() == 0


def test_toggle_favorite_add_is_idempotent(db_session, buyer, published_event):
    social_service.toggle_favorite(db_session, buyer.id, published_event.id, add=True)
    social_service.toggle_favorite(db_session, buyer.id, published_event.id, add=True)
    assert db_session.query(Favorite).filter_by(user_id=buyer.id, event_id=published_event.id).count() == 1


def test_toggle_organizer_follow(db_session, buyer, organizer):
    social_service.toggle_organizer_follow(db_session, buyer.id, organizer.id, add=True)
    assert social_service.organizer_follower_count(db_session, organizer.id) == 1

    social_service.toggle_organizer_follow(db_session, buyer.id, organizer.id, add=False)
    assert social_service.organizer_follower_count(db_session, organizer.id) == 0
    assert db_session.query(OrganizerFollow).count() == 0


def test_toggle_instructor_follow(db_session, buyer):
    instructor = Instructor(name="مدرس تست")
    db_session.add(instructor)
    db_session.commit()
    db_session.refresh(instructor)

    social_service.toggle_instructor_follow(db_session, buyer.id, instructor.id, add=True)
    assert social_service.instructor_follower_count(db_session, instructor.id) == 1

    social_service.toggle_instructor_follow(db_session, buyer.id, instructor.id, add=False)
    assert db_session.query(InstructorFollow).count() == 0
