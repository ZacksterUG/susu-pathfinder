"""Тесты ручки POST /path."""

from unittest.mock import AsyncMock


class TestFindPath:
    def test_returns_path_when_found(self, client, mock_repositories):
        response = client.post("/path", json={
            "building_id": "bc1c5554-bcc6-499f-884d-25b8b5e42ad8",
            "start_object_id": "room-101",
            "end_object_id": "room-102",
        })
        assert response.status_code == 200

    def test_returns_error_different_buildings(self, client, mock_repositories):
        mock_repositories["path"].get_room_by_id = AsyncMock(side_effect=[
            {"id": "room-101", "building_id": "building-a", "floor_number": "1",
             "coordinates": {"points": [{"x": 10, "y": 10}]}},
            {"id": "room-201", "building_id": "building-b", "floor_number": "1",
             "coordinates": {"points": [{"x": 20, "y": 20}]}},
        ])
        response = client.post("/path", json={
            "building_id": "any",
            "start_object_id": "room-101",
            "end_object_id": "room-201",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is False
        assert "different buildings" in data["error"]

    def test_returns_404_when_start_not_found(self, client, mock_repositories):
        mock_repositories["path"].get_room_by_id = AsyncMock(side_effect=[None, {}])
        response = client.post("/path", json={
            "building_id": "bc1c5554-bcc6-499f-884d-25b8b5e42ad8",
            "start_object_id": "nonexistent",
            "end_object_id": "room-102",
        })
        assert response.status_code == 404

    def test_returns_404_when_end_not_found(self, client, mock_repositories):
        mock_repositories["path"].get_room_by_id = AsyncMock(side_effect=[
            {"id": "room-101", "building_id": "bc1c5554", "floor_number": "1",
             "coordinates": {"points": [{"x": 10, "y": 10}]}},
            None,
        ])
        response = client.post("/path", json={
            "building_id": "bc1c5554-bcc6-499f-884d-25b8b5e42ad8",
            "start_object_id": "room-101",
            "end_object_id": "nonexistent",
        })
        assert response.status_code == 404


class TestHealth:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
