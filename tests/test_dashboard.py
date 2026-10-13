def test_dashboard_loads_and_has_database_statistics(client, add_medicine):
    add_medicine(quantity="14", min_stock="10")
    response = client.get("/")
    assert response.status_code == 200
    assert b"Medicine types tracked" in response.data
    assert b"14" in response.data


def test_health_checks_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "database": "ok"}
