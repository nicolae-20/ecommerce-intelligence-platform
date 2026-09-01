from pathlib import Path
import sys

from fastapi import APIRouter
from ai_assistant import ask_assistant

sys.path.append(str(Path(__file__).resolve().parents[2] / "python"))

from analytics import (
    approve_transaction_category,
    assign_transaction_category,
    cancel_transaction_rejection,
    get_bookkeeping_categories,
    get_bookkeeping_summary,
    get_transactions_requiring_review,
    reject_transaction_category,
    get_reconciliation_review_queue,
    confirm_bank_transaction_match,
    reject_bank_transaction_match,
    investigate_bank_transaction,
    get_audit_log,
    run_reconciliation,
    categorize_uncategorized_transactions,
    get_ai_categorization_review_queue,
)

from api.schemas.bookkeeping import (
    BookkeepingCategory,
    BookkeepingSummary,
    ReviewTransaction,
    TransactionActionResponse,
    ReconciliationReviewItem,
    AuditLogItem,
    AIAssistantRequest,
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
        amount=row[4],
        category=row[5],
        vendor=row[6],
        ai_suggested_category=row[7],
        ai_confidence=row[8],
        reconciliation_status=row[9],
        status=row[10],
        ai_review_status=row[11],
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
            message="Category assignment failed.",
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


@router.get(
    "/reconciliation-review",
    response_model=list[ReconciliationReviewItem],
)
def reconciliation_review():
    rows = get_reconciliation_review_queue()

    return [
        ReconciliationReviewItem(
            bank_transaction_id=row[0],
            bank_date=row[1].isoformat(),
            bank_description=row[2],
            bank_amount=float(row[3]),
            status=row[4],
            financial_transaction_id=row[5],
            match_type=row[6],
            match_confidence=float(row[7]),
            system_date=row[8].isoformat() if row[8] else None,
            system_description=row[9],
            system_amount=float(row[10]) if row[10] is not None else None,
        )
        for row in rows
    ]


@router.post(
    "/reconciliation/{bank_transaction_id}/confirm",
    response_model=TransactionActionResponse,
)
def confirm_reconciliation(bank_transaction_id: int):
    success = confirm_bank_transaction_match(bank_transaction_id)

    if not success:
        return TransactionActionResponse(
            success=False,
            message="Reconciliation match could not be confirmed.",
        )

    return TransactionActionResponse(
        success=True,
        message="Reconciliation match confirmed successfully.",
    )



@router.post(
    "/reconciliation/{bank_transaction_id}/reject",
    response_model=TransactionActionResponse,
)
def reject_reconciliation(bank_transaction_id: int):
    success = reject_bank_transaction_match(bank_transaction_id)

    if not success:
        return TransactionActionResponse(
            success=False,
            message="Reconciliation match could not be rejected.",
        )

    return TransactionActionResponse(
        success=True,
        message="Reconciliation match rejected successfully.",
    )

@router.post(
    "/reconciliation/{bank_transaction_id}/investigate",
    response_model=TransactionActionResponse,
)
def investigate_reconciliation(bank_transaction_id: int):
    success = investigate_bank_transaction(bank_transaction_id)

    if not success:
        return TransactionActionResponse(
            success=False,
            message="Bank transaction could not be marked as investigated.",
        )

    return TransactionActionResponse(
        success=True,
        message="Bank transaction marked as investigated.",
    )


@router.get(
    "/audit-log",
    response_model=list[AuditLogItem],
)
def audit_log():
    rows = get_audit_log()

    return [
        AuditLogItem(
            audit_id=row[0],
            bank_transaction_id=row[1],
            financial_transaction_id=row[2],
            action=row[3],
            details=row[4],
            created_at=row[5].isoformat(),
        )
        for row in rows
    ]

@router.post(
    "/reconciliation/run",
    response_model=TransactionActionResponse,
)
def run_reconciliation_endpoint():
    success = run_reconciliation()

    if not success:
        return TransactionActionResponse(
            success=False,
            message="Reconciliation could not be completed.",
        )

    return TransactionActionResponse(
        success=True,
        message="Reconciliation completed successfully.",
    )


@router.post(
    "/ai-categorize",
)
def ai_categorize_transactions():
    results = categorize_uncategorized_transactions()

    if not results:
        return {
            "success": True,
            "message": "No uncategorized transactions require AI categorization.",
            "count": 0,
            "results": [],
        }

    return {
        "success": True,
        "message": "AI categorization completed successfully.",
        "count": len(results),
        "results": results,
    }

@router.get(
    "/ai-review-queue",
    response_model=list[ReviewTransaction],
)
def ai_review_queue():
    rows = get_ai_categorization_review_queue()

    return [
        ReviewTransaction(
            transaction_id=row[0],
            transaction_date=row[1].isoformat(),
            transaction_type=row[2],
            description=row[3],
            amount=row[4],
            category=row[5],
            vendor=row[6],
            ai_suggested_category=row[7],
            ai_confidence=row[8],
            reconciliation_status=row[9],
            status=row[10],
            ai_review_status=row[11],
        )
        for row in rows
    ]


@router.post("/ai-assistant")
def ai_assistant(request: AIAssistantRequest):
    response = ask_assistant(request.question)

    return {
        "success": True,
        "message": response.message,
        "tool_name": response.tool_name,
        "tool_result": response.tool_result,
    }