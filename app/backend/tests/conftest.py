"""Фикстуры и мок-данные для тестов."""

from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ─── Мок-данные ──────────────────────────────────────────────

MOCK_BUILDING = {
    "id": "bc1c5554-bcc6-499f-884d-25b8b5e42ad8",
    "name": "Учебный корпус №3бв",
    "short_name": "3б",
}

MOCK_FLOOR = {
    "id": "f1",
    "building_id": MOCK_BUILDING["id"],
    "floor_number": "1",
    "corridor_points": {"points": [{"x": 0, "y": 0}, {"x": 100, "y": 100}]},
}

MOCK_ROOM = {
    "id": "room-101",
    "building_id": MOCK_BUILDING["id"],
    "floor_number": "1",
    "number": "101",
    "name": "Учебная аудитория",
    "room_type": "Учебная аудитория",
    "coordinates": {"points": [{"x": 10, "y": 10}, {"x": 50, "y": 50}]},
}

MOCK_TECHNICAL = {
    "id": "tech-stairs-1",
    "building_id": MOCK_BUILDING["id"],
    "floor_number": "1",
    "name": "Лестница",
    "type": "Лестница",
    "coordinates": {"points": [{"x": 100, "y": 100}]},
    "has_entrance": True,
    "linked": ["tech-stairs-2"],
}

MOCK_ENTRANCE = {
    "object_id": "ent-1",
    "object_type": "stairs",
    "building_id": MOCK_BUILDING["id"],
    "floor_number": "1",
    "x": 260,
    "y": 136,
    "room_number": "Лестница 1",
}


# ─── Фикстуры ────────────────────────────────────────────────

@pytest.fixture
def client():
    """TestClient для FastAPI приложения."""
    return TestClient(app)


@pytest.fixture
def mock_repositories():
    """Мок всех функций репозитория."""
    with patch("app.routers.buildings.repositories") as mock_bld, \
         patch("app.routers.floors.repositories") as mock_flr, \
         patch("app.routers.rooms.repositories") as mock_rm, \
         patch("app.routers.technical.repositories") as mock_tech, \
         patch("app.routers.entrances.repositories") as mock_ent, \
         patch("app.routers.path.repositories") as mock_path:

        # buildings
        mock_bld.get_building = AsyncMock(return_value=MOCK_BUILDING)
        mock_bld.get_all_buildings = AsyncMock(return_value=[MOCK_BUILDING])

        # floors
        mock_flr.get_building = AsyncMock(return_value=MOCK_BUILDING)
        mock_flr.get_floors_by_building = AsyncMock(return_value=[MOCK_FLOOR])

        # rooms
        mock_rm.get_building = AsyncMock(return_value=MOCK_BUILDING)
        mock_rm.get_rooms_by_floor = AsyncMock(return_value=[MOCK_ROOM])

        # technical
        mock_tech.get_building = AsyncMock(return_value=MOCK_BUILDING)
        mock_tech.get_technical_by_floor = AsyncMock(return_value=[MOCK_TECHNICAL])

        # entrances
        mock_ent.get_building = AsyncMock(return_value=MOCK_BUILDING)
        mock_ent.get_entrances_by_floor = AsyncMock(return_value=[MOCK_ENTRANCE])

        # path
        mock_path.get_room_by_id = AsyncMock(return_value=MOCK_ROOM)
        mock_path.get_cached_path = AsyncMock(return_value=None)
        mock_path.get_floors_by_building = AsyncMock(return_value=[MOCK_FLOOR])
        mock_path.get_technical_by_floor = AsyncMock(return_value=[MOCK_TECHNICAL])
        mock_path.get_entrances_by_floor = AsyncMock(return_value=[MOCK_ENTRANCE])
        mock_path.get_grid_by_floor = AsyncMock(return_value=None)
        mock_path.save_cached_path = AsyncMock()

        yield {
            "buildings": mock_bld,
            "floors": mock_flr,
            "rooms": mock_rm,
            "technical": mock_tech,
            "entrances": mock_ent,
            "path": mock_path,
        }
