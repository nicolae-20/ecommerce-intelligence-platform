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


class TransactionActionResponse(BaseModel):
    success: bool
    message: str


class BookkeepingCategory(BaseModel):
    category_id: int
    account_code: str
    account_name: str
    account_type: str


class ReconciliationReviewItem(BaseModel):
    bank_transaction_id: int
    bank_date: str
    bank_description: str | None
    bank_amount: float
    status: str
    financial_transaction_id: int | None
    match_type: str
    match_confidence: float
    system_date: str | None
    system_description: str | None
    system_amount: float | None