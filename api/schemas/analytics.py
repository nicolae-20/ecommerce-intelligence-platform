from pydantic import BaseModel


class MonthlyRevenue(BaseModel):
    order_month: str
    monthly_revenue: float


class CategoryProfit(BaseModel):
    category_name: str
    revenue: float
    cost: float
    profit: float