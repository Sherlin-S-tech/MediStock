def test_csv_report_generation_and_escaping(client, add_medicine, medicine_data):
    add_medicine(name='Tablet, "C"', batch_number="CSV-1")
    response = client.get("/reports/inventory.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b'"Tablet, ""C"""' in response.data
    assert b"Batch Number" in response.data


def test_expired_and_low_stock_report(client, add_medicine):
    add_medicine(expiry_date="2026-10-12", quantity="3", min_stock="5")
    assert b"TEST-001" in client.get("/reports/expired.csv").data
    assert b"TEST-001" in client.get("/reports/low-stock.csv").data


def test_unknown_report_is_not_found(client):
    assert client.get("/reports/unknown.csv").status_code == 404
