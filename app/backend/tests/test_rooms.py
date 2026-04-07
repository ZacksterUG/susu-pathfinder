"""Тесты ручки GET /buildings/{id}/floors/{n}/rooms."""


class TestListRooms:
    def test_returns_rooms(self, client, mock_repositories):
        bid = "bc1c5554-bcc6-499f-884d-25b8b5e42ad8"
        response = client.get(f"/buildings/{bid}/floors/1/rooms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["number"] == "101"
        assert data[0]["room_type"] == "Учебная аудитория"
        assert data[0]["coordinates"] is not None

    def test_returns_404_when_building_not_found(self, client, mock_repositories):
        mock_repositories["rooms"].get_building.return_value = None
        response = client.get("/buildings/nonexistent/floors/1/rooms")
        assert response.status_code == 404
