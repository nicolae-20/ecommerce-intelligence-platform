from pathlib import Path
import sys

from fastapi import APIRouter

sys.path.append(str(Path(__file__).resolve().parents[2] / "python"))

from analytics import (
    approve_transaction_category,
    assign_transaction_category,
    cancel_transaction_rejection,
    get_bookkeeping_categories,
    get_bookkeeping_summary,
    get_transactions_requiring_review,
    reject_transaction_category,
)

from api.schemas.bookkeeping import (
    BookkeepingCategory,
    BookkeepingSummary,
    ReviewTransaction,
    TransactionActionResponse,
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


@router.post(
    "/transactions/{transaction_id}/approve",
    response_model=TransactionActionResponse,
)
def approve_transaction(transaction_id: int):
    success = approve_transaction_category(transaction_id)

    if not success:
        return TransactionActionResponse(
            success=False,
            message="Transaction could not be approved.",
        )

    return TransactionActionResponse(
        success=True,
        message="AI category suggestion approved successfully.",
    )

@router.post(
    "/transactions/{transaction_id}/reject",
    response_model=TransactionActionResponse,
)
def reject_transaction(transaction_id: int):
    success = reject_transaction_category(transaction_id)

    if not success:
        return TransactionActionResponse(
            success=False,
            message="Transaction could not be rejected.",
        )

    return TransactionActionResponse(
        success=True,
        message="AI category suggestion rejected.",
    )


@router.get(
    "/categories",
    response_model=list[BookkeepingCategory],
)
def bookkeeping_categories():
    rows = get_bookkeeping_categories()

    return [
    BookkeepingCategory(
        category_id=row[0],
        account_code=row[1],
        account_name=row[2],
        account_type=row[3],
    )
    for row in rows
]


@router.post(
    "/transactions/{transaction_id}/category/{category_id}",
    response_model=TransactionActionResponse,
)
def assign_category(transaction_id: int, category_id: int):
    success = assign_transaction_category(
        transaction_id,
        category_id,
    )

    if not success:
        return TransactionActionResponse(
            success=False,
            message="Transaction category could not be assigned.",
        )

    return TransactionActionResponse(
        success=True,
        message="Transaction category assigned successfully.",
    )

@router.post(
    "/transactions/{transaction_id}/cancel-reject",
    response_model=TransactionActionResponse,
)
def cancel_reject(transaction_id: int):
    success = cancel_transaction_rejection(transaction_id)

    if not success:
        return TransactionActionResponse(
            success=False,
            message="Transaction rejection could not be cancelled.",
        )

    return TransactionActionResponse(
        success=True,
        message="AI category suggestion restored.",
    )