import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))

from analytics import get_customer_metrics, get_monthly_revenue, get_top_customers


def test_top_customers():
    customers = get_top_customers(5)

    assert len(customers) == 5
    assert customers[0][0] == "Andrei Popescu"


def test_monthly_revenue():
    revenue = get_monthly_revenue()

    assert len(revenue) == 3
    assert revenue[0][0] == "2026-01"


def test_customer_metrics():
    metrics = get_customer_metrics()

    assert len(metrics) > 0
    assert metrics[0][0] == 1