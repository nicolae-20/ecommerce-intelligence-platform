from pathlib import Path
import sys

from fastapi import APIRouter
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[2] / "python"))

from analytics import get_monthly_revenue


router = APIRouter(prefix="/analytics", tags=["analytics"])


from api.schemas.analytics import MonthlyRevenue

from analytics import get_monthly_revenue, get_profit_by_category
from api.schemas.analytics import CategoryProfit, MonthlyRevenue


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