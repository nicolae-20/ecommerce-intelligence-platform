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


def test_profit_by_category():
    response = client.get("/analytics/profit-by-category")

    assert response.status_code == 200

    data = response.json()

    assert len(data) > 0
    assert "category_name" in data[0]
    assert "revenue" in data[0]
    assert "cost" in data[0]
    assert "profit" in data[0]

def test_overview():
    response = client.get("/analytics/overview")

    assert response.status_code == 200

    data = response.json()

    assert data["total_revenue"] > 0
    assert data["total_orders"] > 0
    assert data["total_customers"] > 0
    assert data["average_order_value"] > 0