from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_top_customers():
    response = client.get("/customers/top")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 5
    assert data[0]["customer_name"] == "Andrei Popescu"


def test_monthly_revenue():
    response = client.get("/analytics/monthly-revenue")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3
    assert data[0]["order_month"] == "2026-01"


def test_customer_metrics():
    response = client.get("/customers/metrics")

    assert response.status_code == 200

    data = response.json()

    assert len(data) > 0
    assert data[0]["customer_id"] == 1