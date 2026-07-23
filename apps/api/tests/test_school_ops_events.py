"""School operations event API regressions."""

from __future__ import annotations

import uuid
from datetime import date, time

import pytest

from app.db.models.school_ops import Event
from app.modules.school_ops.schemas.ops import EventOut
from tests.conftest import access_token_for, auth_headers


def test_event_out_serializes_database_time() -> None:
    event = Event(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        school_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        title="Pilot Orientation",
        event_date=date(2026, 7, 23),
        event_time=time(14, 30),
        created_by=uuid.UUID("00000000-0000-0000-0000-000000000003"),
    )

    serialized = EventOut.model_validate(event)

    assert serialized.event_time == "14:30"


@pytest.mark.asyncio
async def test_list_events_serializes_database_time(client, db_session, admin_user) -> None:
    event = Event(
        school_id=admin_user.school_id,
        title="Pilot Orientation",
        event_date=date(2026, 7, 23),
        event_time=time(14, 30),
        venue="Conference Room",
        target_roles=["admin", "teacher"],
        created_by=admin_user.id,
    )
    db_session.add(event)
    await db_session.flush()

    token = access_token_for(admin_user)
    response = await client.get("/api/v1/ops/events", headers=auth_headers(token))

    assert response.status_code == 200, response.text
    matching = [item for item in response.json()["data"] if item["id"] == str(event.id)]
    assert matching == [
        {
            "id": str(event.id),
            "title": "Pilot Orientation",
            "description": None,
            "event_date": "2026-07-23",
            "event_time": "14:30",
            "venue": "Conference Room",
            "target_roles": ["admin", "teacher"],
        }
    ]
