"""Тесты ручки GET /buildings/{id}/floors."""


class TestListFloors:
    def test_returns_floors(self, client, mock_repositories):
        bid = "bc1c5554-bcc6-499f-884d-25b8b5e42ad8"
        response = client.get(f"/buildings/{bid}/floors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["floor_number"] == "1"
        assert data[0]["corridor_points"] is not None

    def test_returns_404_when_building_not_found(self, client, mock_repositories):
        mock_repositories["floors"].get_building.return_value = None
        response = client.get("/buildings/nonexistent/floors")
        assert response.status_code == 404
