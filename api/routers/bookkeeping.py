from pathlib import Path
import sys

from fastapi import APIRouter

sys.path.append(str(Path(__file__).resolve().parents[2] / "python"))

from analytics import (
    get_bookkeeping_summary,
    get_transactions_requiring_review,
)
from api.schemas.bookkeeping import (
    BookkeepingSummary,
    ReviewTransaction,
)


router = APIRouter(prefix="/bookkeeping", tags=["bookkeeping"])


@router.get("/summary", response_model=BookkeepingSummary)
def bookkeeping_summary():
    row = get_bookkeeping_summary()

    return BookkeepingSummary(
        total_revenue=float(row[0] or 0),
        total_expenses=float(row[1] or 0),
        net_movement=float(row[2] or 0),
        transactions_requiring_review=row[3] or 0,
    )


@router.get(
    "/review-queue",
    response_model=list[ReviewTransaction],
)
def review_queue():
    rows = get_transactions_requiring_review()

    return [
        ReviewTransaction(
            transaction_id=row[0],
            transaction_date=row[1].isoformat(),
            transaction_type=row[2],
            description=row[3],
            amount=float(row[4]),
            category=row[5],
            vendor=row[6],
            ai_suggested_category=row[7],
            ai_confidence=float(row[8]) if row[8] is not None else None,
            reconciliation_status=row[9],
            status=row[10],
        )
        for row in rows
    ]