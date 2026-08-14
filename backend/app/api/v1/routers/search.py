from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.rate_limit_middleware import limiter
from app.schemas.search import SearchResultOut, SearchSuggestionsOut
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResultOut)
@limiter.limit("30/minute")
def search(
    request: Request,
    q: str = Query(min_length=1, max_length=200),
    category_id: int | None = None,
    format: str | None = None,
    db: Session = Depends(get_db),
):
    people = search_service.search_people(db, q)
    events = search_service.search_events(db, q, category_id=category_id, format=format)
    return SearchResultOut(people=people, events=events)


@router.get("/suggestions", response_model=SearchSuggestionsOut)
def suggestions(q: str = Query(min_length=1, max_length=200), db: Session = Depends(get_db)):
    return SearchSuggestionsOut(suggestions=search_service.suggest(db, q))
