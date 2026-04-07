"""Тесты ручки GET /buildings."""


class TestListBuildings:
    def test_returns_buildings(self, client, mock_repositories):
        response = client.get("/buildings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "bc1c5554-bcc6-499f-884d-25b8b5e42ad8"
        assert data[0]["name"] == "Учебный корпус №3бв"
        assert data[0]["short_name"] == "3б"


class TestGetBuilding:
    def test_returns_building(self, client, mock_repositories):
        bid = "bc1c5554-bcc6-499f-884d-25b8b5e42ad8"
        response = client.get(f"/buildings/{bid}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bid
        assert data["name"] == "Учебный корпус №3бв"

    def test_returns_404_when_not_found(self, client, mock_repositories):
        mock_repositories["buildings"].get_building.return_value = None
        response = client.get("/buildings/nonexistent")
        assert response.status_code == 404
