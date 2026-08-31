import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))

from analytics import (
    get_accounting_insights,
    get_bookkeeping_summary,
    get_customer_metrics,
    get_financial_summary,
    get_monthly_revenue,
    get_top_customers,
    get_transactions_requiring_review,
)

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


def test_financial_summary():
    summary = get_financial_summary()

    assert summary[0] == 6236.8
    assert summary[1] == 3909
    assert summary[2] == 2327.8
    assert summary[3] == 37.32

def test_accounting_insights():
    insights = get_accounting_insights()

    assert len(insights) == 4
    assert insights[0]["type"] == "financial_summary"
    assert insights[1]["type"] == "margin"
    assert insights[2]["type"] == "top_category"
    assert insights[3]["type"] == "bottom_category"


def test_bookkeeping_summary():
    summary = get_bookkeeping_summary()

    assert summary[0] == 950
    assert summary[1] == 228.5
    assert summary[2] == 721.5
    assert summary[3] == 3


def test_transactions_requiring_review():
    transactions = get_transactions_requiring_review()

    assert len(transactions) == 3

    assert transactions[0][0] == 1
    assert transactions[0][7] == "Software"

    assert transactions[1][0] == 4
    assert transactions[1][7] == "Bank Fees"

    assert transactions[2][0] == 5
    assert transactions[2][7] == "Software"