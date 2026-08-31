from pydantic import BaseModel


class MonthlyRevenue(BaseModel):
    order_month: str
    monthly_revenue: float


class CategoryProfit(BaseModel):
    category_name: str
    revenue: float
    cost: float
    profit: float

class Overview(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    average_order_value: float


class FinancialSummary(BaseModel):
    total_revenue: float
    total_cogs: float
    gross_profit: float
    gross_margin: float