import pytest
from app import create_app


@pytest.fixture()
def app(tmp_path):
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE": str(tmp_path / "isolated-test.db"),
        "TODAY": "2026-10-13",
        "WTF_CSRF_ENABLED": False,
    })
    yield test_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def medicine_data():
    return {
        "name": "Test Paracetamol", "batch_number": "TEST-001", "category": "Analgesic",
        "manufacturer": "Fictional Labs", "quantity": "100", "min_stock": "10",
        "manufacturing_date": "2026-01-01", "expiry_date": "2027-01-01",
        "unit_price": "2.50", "supplier": "Demo Supply Co",
    }


@pytest.fixture()
def add_medicine(client, medicine_data):
    def _add(**changes):
        data = {**medicine_data, **changes}
        response = client.post("/medicines/new", data=data, follow_redirects=True)
        return response
    return _add
