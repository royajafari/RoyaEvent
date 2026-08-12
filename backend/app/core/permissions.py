from fastapi import HTTPException, status

from app.models.event import Event
from app.models.user import User


def require_event_owner(event: Event, user: User) -> None:
    if event.organizer_id != user.id and user.role.value != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "شما مالک این رویداد نیستید")
