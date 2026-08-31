from pathlib import Path
import sys

from fastapi import APIRouter
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[2] / "python"))

from analytics import get_monthly_revenue


router = APIRouter(prefix="/analytics", tags=["analytics"])


from api.schemas.analytics import MonthlyRevenue

from analytics import (
    get_financial_summary,
    get_monthly_revenue,
    get_overview,
    get_profit_by_category,
)

from api.schemas.analytics import (
    CategoryProfit,
    FinancialSummary,
    MonthlyRevenue,
    Overview,
)

@router.get("/overview", response_model=Overview)
def overview():
    row = get_overview()

    return Overview(
        total_revenue=float(row[0] or 0),
        total_orders=row[1] or 0,
        total_customers=row[2] or 0,
        average_order_value=float(row[3] or 0)
    )


@router.get("/monthly-revenue", response_model=list[MonthlyRevenue])
def monthly_revenue():
    rows = get_monthly_revenue()

    return [
        MonthlyRevenue(
            order_month=row[0],
            monthly_revenue=float(row[1])
        )
        for row in rows
    ]


@router.get("/profit-by-category", response_model=list[CategoryProfit])
def profit_by_category():
    rows = get_profit_by_category()

    return [
        CategoryProfit(
            category_name=row[0],
            revenue=float(row[1]),
            cost=float(row[2]),
            profit=float(row[3])
        )
        for row in rows
    ]


@router.get("/financial-summary", response_model=FinancialSummary)
def financial_summary():
    row = get_financial_summary()

    return FinancialSummary(
        total_revenue=float(row[0] or 0),
        total_cogs=float(row[1] or 0),
        gross_profit=float(row[2] or 0),
        gross_margin=float(row[3] or 0),
    )