"""Тесты ручки GET /buildings/{id}/floors/{n}/entrances."""


class TestListEntrances:
    def test_returns_entrances(self, client, mock_repositories):
        bid = "bc1c5554-bcc6-499f-884d-25b8b5e42ad8"
        response = client.get(f"/buildings/{bid}/floors/1/entrances")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["object_type"] == "stairs"
        assert data[0]["x"] == 260
        assert data[0]["y"] == 136
        assert data[0]["room_number"] == "Лестница 1"

    def test_returns_404_when_building_not_found(self, client, mock_repositories):
        mock_repositories["entrances"].get_building.return_value = None
        response = client.get("/buildings/nonexistent/floors/1/entrances")
        assert response.status_code == 404
