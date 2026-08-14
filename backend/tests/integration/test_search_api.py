import hashlib
from datetime import datetime, timedelta

import chromadb
import pytest


def _future_iso(hours: int) -> str:
    return (datetime.now() + timedelta(hours=hours)).isoformat()


def _event_payload(category_id: int, **overrides) -> dict:
    payload = {
        "title": "کارگاه آموزشی هوش مصنوعی",
        "description": "توضیحات کامل کارگاه هوش مصنوعی برای مبتدیان",
        "category_id": category_id,
        "format": "online",
        "online_platform_name": "SkyRoom",
        "visibility": "public",
        "sessions": [{"starts_at": _future_iso(48), "duration_minutes": 90}],
    }
    payload.update(overrides)
    return payload


def _fake_embed(text: str, dim: int = 32) -> list[float]:
    """embedding قلابی و سریع برای تست — بدون دانلود/اجرای مدل واقعی. بردار
    بر اساس حضور کلمات (bag-of-words هش‌شده) ساخته می‌شه، پس متن‌های
    هم‌کلمه به هم نزدیک‌تر می‌مونن، دقیقاً چیزی که برای تست ترتیب لازم داریم."""
    vec = [0.0] * dim
    for word in text.split():
        idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % dim
        vec[idx] += 1.0
    norm = sum(v * v for v in vec) ** 0.5
    return [v / norm for v in vec] if norm > 0 else [1.0] + [0.0] * (dim - 1)


@pytest.fixture()
def fake_search_backend(monkeypatch):
    """جایگزینی کلاینت Chroma با نسخه‌ی in-memory (EphemeralClient) و مدل
    embedding واقعی با یک تابع سریع/قطعی — تست‌های این فایل رفتار واقعی
    sync_event_index رو (که در conftest.py به‌صورت پیش‌فرض no-op شده) با
    این بک‌اند قلابی دوباره فعال می‌کنن."""
    import app.search.chroma_client as chroma_client_module
    import app.search.indexer as indexer_module
    import app.services.event_service as event_service_module
    import app.services.search_service as search_service_module

    client = chromadb.EphemeralClient()
    monkeypatch.setattr(chroma_client_module, "get_chroma_client", lambda: client)
    monkeypatch.setattr(indexer_module, "embed_text", _fake_embed)
    monkeypatch.setattr(search_service_module, "embed_text", _fake_embed)
    monkeypatch.setattr(event_service_module, "sync_event_index", indexer_module.sync_event_index)
    yield client


def test_search_finds_published_event_by_content(
    client, leaf_category, auth_headers, fake_search_backend
):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]
    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)

    resp = client.get("/api/v1/search", params={"q": "هوش مصنوعی"})
    assert resp.status_code == 200
    body = resp.json()
    ids = [e["id"] for e in body["events"]]
    assert event_id in ids


def test_search_excludes_draft_events(client, leaf_category, auth_headers, fake_search_backend):
    create_resp = client.post(
        "/api/v1/events",
        json=_event_payload(leaf_category.id, title="رویداد پیش‌نویس محرمانه"),
        headers=auth_headers,
    )
    event_id = create_resp.json()["id"]
    # عمداً publish نمی‌کنیم — باید طبق قاعده‌ی دائمی امنیتی از جستجو غایب باشه

    resp = client.get("/api/v1/search", params={"q": "پیش‌نویس محرمانه"})
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["events"]]
    assert event_id not in ids


def test_search_excludes_cancelled_events(client, leaf_category, auth_headers, fake_search_backend):
    create_resp = client.post(
        "/api/v1/events",
        json=_event_payload(leaf_category.id, title="رویداد لغوشده خاص"),
        headers=auth_headers,
    )
    event_id = create_resp.json()["id"]
    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)
    client.delete(f"/api/v1/events/{event_id}", headers=auth_headers)

    resp = client.get("/api/v1/search", params={"q": "لغوشده خاص"})
    ids = [e["id"] for e in resp.json()["events"]]
    assert event_id not in ids


def test_search_filters_by_category(client, leaf_category, auth_headers, fake_search_backend):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    event_id = create_resp.json()["id"]
    client.post(f"/api/v1/events/{event_id}/publish", headers=auth_headers)

    resp = client.get(
        "/api/v1/search", params={"q": "هوش مصنوعی", "category_id": leaf_category.id + 999}
    )
    ids = [e["id"] for e in resp.json()["events"]]
    assert event_id not in ids


def test_search_requires_query_param(client):
    resp = client.get("/api/v1/search")
    assert resp.status_code == 422


def test_search_finds_instructor_by_name_prefix(client, db_session, fake_search_backend):
    from app.models.instructor import Instructor

    instructor = Instructor(name="سارا احمدی")
    db_session.add(instructor)
    db_session.commit()

    resp = client.get("/api/v1/search", params={"q": "سارا"})
    people = resp.json()["people"]
    assert any(p["type"] == "instructor" and p["name"] == "سارا احمدی" for p in people)


def test_search_finds_organizer_with_published_event(
    client, leaf_category, auth_headers, organizer, fake_search_backend
):
    create_resp = client.post(
        "/api/v1/events", json=_event_payload(leaf_category.id), headers=auth_headers
    )
    client.post(f"/api/v1/events/{create_resp.json()['id']}/publish", headers=auth_headers)

    resp = client.get("/api/v1/search", params={"q": organizer.full_name[:4]})
    people = resp.json()["people"]
    assert any(p["type"] == "organizer" and p["id"] == organizer.id for p in people)


def test_search_suggestions_matches_title(client, leaf_category, auth_headers, fake_search_backend):
    create_resp = client.post(
        "/api/v1/events",
        json=_event_payload(leaf_category.id, title="دوره‌ی ویژه‌ی پایتون"),
        headers=auth_headers,
    )
    client.post(f"/api/v1/events/{create_resp.json()['id']}/publish", headers=auth_headers)

    resp = client.get("/api/v1/search/suggestions", params={"q": "پایتون"})
    assert resp.status_code == 200
    assert "دوره‌ی ویژه‌ی پایتون" in resp.json()["suggestions"]
