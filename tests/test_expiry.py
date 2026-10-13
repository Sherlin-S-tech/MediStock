from datetime import date
from services import classify_expiry


def test_expiry_groups_use_configured_clock(client, add_medicine):
    add_medicine(batch_number="OLD", name="Old medicine", expiry_date="2026-10-12")
    add_medicine(batch_number="SOON", name="Soon medicine", expiry_date="2026-11-12")
    add_medicine(batch_number="GOOD", name="Good medicine", expiry_date="2026-11-13")
    response = client.get("/expiry")
    assert b"Old medicine" in response.data
    assert b"Soon medicine" in response.data
    assert b"Good medicine" in response.data


def test_expiry_classification_boundary_inclusive():
    today = date(2026, 10, 13)
    assert classify_expiry("2026-10-12", today) == "Expired"
    assert classify_expiry("2026-10-13", today) == "Near expiry"
    assert classify_expiry("2026-11-12", today) == "Near expiry"
    assert classify_expiry("2026-11-13", today) == "Valid"
