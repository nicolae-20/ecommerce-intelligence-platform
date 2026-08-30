from pathlib import Path
import sys

from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi import HTTPException

sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))

from analytics import (
    get_customer,
    get_customer_metrics,
    get_monthly_revenue,
    get_top_customers,
)


app = FastAPI()

class CustomerMetrics(BaseModel):
    customer_id: int
    customer_name: str
    total_orders: int
    total_items: int
    total_revenue: float

class CustomerRevenue(BaseModel):
    customer_name: str
    total_revenue: float


class MonthlyRevenue(BaseModel):
    order_month: str
    monthly_revenue: float

class Customer(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    country: str


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer_by_id(customer_id: int):
    row = get_customer(customer_id)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return Customer(
        customer_id=row[0],
        first_name=row[1],
        last_name=row[2],
        country=row[3]
    )

@app.get("/customers/top", response_model=list[CustomerRevenue])
def top_customers(limit: int = Query(default=5, ge=1, le=20)):
    rows = get_top_customers(limit)

    return [
        CustomerRevenue(
            customer_name=row[0],
            total_revenue=float(row[1])
        )
        for row in rows
    ]


@app.get("/analytics/monthly-revenue", response_model=list[MonthlyRevenue])
def monthly_revenue():
    rows = get_monthly_revenue()

    return [
        MonthlyRevenue(
            order_month=row[0],
            monthly_revenue=float(row[1])
        )
        for row in rows
    ]


@app.get("/customers/metrics", response_model=list[CustomerMetrics])
def customer_metrics():
    rows = get_customer_metrics()

    return [
        CustomerMetrics(
            customer_id=row[0],
            customer_name=row[1],
            total_orders=row[2],
            total_items=row[3],
            total_revenue=float(row[4])
        )
        for row in rows
    ]