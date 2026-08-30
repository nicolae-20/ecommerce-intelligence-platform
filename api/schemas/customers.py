from pydantic import BaseModel


class CustomerRevenue(BaseModel):
    customer_name: str
    total_revenue: float


class CustomerMetrics(BaseModel):
    customer_id: int
    customer_name: str
    total_orders: int
    total_items: int
    total_revenue: float


class Customer(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    country: str