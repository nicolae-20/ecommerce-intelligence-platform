from pydantic import BaseModel


class BookkeepingSummary(BaseModel):
    total_revenue: float
    total_expenses: float
    net_movement: float
    transactions_requiring_review: int


class ReviewTransaction(BaseModel):
    transaction_id: int
    transaction_date: str
    transaction_type: str
    description: str | None
    amount: float
    category: str | None
    vendor: str | None
    ai_suggested_category: str | None
    ai_confidence: float | None
    reconciliation_status: str
    status: str