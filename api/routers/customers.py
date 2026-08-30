from pathlib import Path
import sys

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[2] / "python"))

from analytics import get_customer, get_customer_metrics, get_top_customers


router = APIRouter(prefix="/customers", tags=["customers"])


from api.schemas.customers import Customer, CustomerMetrics, CustomerRevenue

@router.get("/top", response_model=list[CustomerRevenue])
def top_customers(limit: int = Query(default=5, ge=1, le=20)):
    rows = get_top_customers(limit)

    return [
        CustomerRevenue(
            customer_name=row[0],
            total_revenue=float(row[1])
        )
        for row in rows
    ]


@router.get("/metrics", response_model=list[CustomerMetrics])
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


@router.get("/{customer_id}", response_model=Customer)
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