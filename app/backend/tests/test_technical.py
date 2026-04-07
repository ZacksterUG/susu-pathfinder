"""Тесты ручки GET /buildings/{id}/floors/{n}/technical."""


class TestListTechnical:
    def test_returns_technical(self, client, mock_repositories):
        bid = "bc1c5554-bcc6-499f-884d-25b8b5e42ad8"
        response = client.get(f"/buildings/{bid}/floors/1/technical")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["type"] == "Лестница"
        assert data[0]["has_entrance"] is True
        assert isinstance(data[0]["linked"], list)

    def test_returns_404_when_building_not_found(self, client, mock_repositories):
        mock_repositories["technical"].get_building.return_value = None
        response = client.get("/buildings/nonexistent/floors/1/technical")
        assert response.status_code == 404
