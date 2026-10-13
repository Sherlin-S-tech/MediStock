def test_add_and_view_medicine(client, add_medicine):
    add_medicine()
    response = client.get("/inventory")
    assert response.status_code == 200
    assert b"Test Paracetamol" in response.data
    assert b"TEST-001" in response.data


def test_reject_invalid_form_values(client, medicine_data):
    response = client.post("/medicines/new", data={**medicine_data, "quantity": "-1", "unit_price": "-2"})
    assert response.status_code == 200
    assert b"cannot be negative" in response.data
    assert b"valid non-negative amount" in response.data


def test_reject_manufacture_after_expiry(client, medicine_data):
    response = client.post("/medicines/new", data={**medicine_data, "manufacturing_date": "2027-02-01", "expiry_date": "2027-01-01"})
    assert b"Manufacturing date cannot be later" in response.data


def test_duplicate_batch_is_rejected(client, add_medicine, medicine_data):
    add_medicine()
    response = client.post("/medicines/new", data={**medicine_data, "name": "Other medicine"})
    assert b"batch number already exists" in response.data


def test_search_and_category_filter(client, add_medicine):
    add_medicine()
    assert b"Test Paracetamol" in client.get("/inventory?q=TEST-001").data
    assert b"Test Paracetamol" in client.get("/inventory?category=Analgesic").data
    assert b"Test Paracetamol" not in client.get("/inventory?q=not-found").data


def test_update_and_delete_medicine(client, add_medicine):
    add_medicine()
    detail = client.get("/medicines/1")
    assert detail.status_code == 200
    update = client.post("/medicines/1/edit", data={"name": "Updated medicine", "batch_number": "TEST-001", "category": "Analgesic", "manufacturer": "Fictional Labs", "quantity": "12", "min_stock": "3", "manufacturing_date": "2026-01-01", "expiry_date": "2027-01-01", "unit_price": "3.25", "supplier": "Demo Supply Co"})
    assert update.status_code == 302
    assert b"Updated medicine" in client.get("/medicines/1").data
    deleted = client.post("/medicines/1/delete")
    assert deleted.status_code == 302
    assert b"Updated medicine" not in client.get("/inventory").data


def test_threshold_is_inclusive_for_low_stock(client, add_medicine):
    add_medicine(quantity="10", min_stock="10")
    assert b"Test Paracetamol" in client.get("/low-stock").data
