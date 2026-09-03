import sys
from pathlib import Path
from llm_categorizer import suggest_transaction_category
from llm_categorizer import (
    AI_CONFIDENCE_THRESHOLD,
    CategorySuggestion,
    is_high_confidence_suggestion,
)

sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))

from analytics import (
    approve_transaction_category,
    get_accounting_insights,
    get_bookkeeping_categories,
    get_bookkeeping_summary,
    get_customer_metrics,
    get_expense_trends,
    get_financial_summary,
    get_monthly_revenue,
    get_revenue_analysis,
    get_spending_by_category,
    get_top_customers,
    get_transactions_requiring_review,
    reject_transaction_category,
    assign_transaction_category,
    cancel_transaction_rejection,
    run_reconciliation,
    get_reconciliation_review_queue,
    reject_bank_transaction_match,
    confirm_bank_transaction_match,
    investigate_bank_transaction,
    log_audit_event,
    get_audit_log,
    get_vendor_totals,
    categorize_transaction_with_llm,
    categorize_uncategorized_transactions,
)

def test_top_customers():
    customers = get_top_customers(5)

    assert len(customers) == 5
    assert customers[0][0] == "Andrei Popescu"


def test_monthly_revenue():
    revenue = get_monthly_revenue()

    assert len(revenue) == 3
    assert revenue[0][0] == "2026-01"


def test_spending_by_category():
    spending = get_spending_by_category()

    assert spending
    assert all(item["category"] is not None for item in spending)
    assert all(float(item["total_spending"]) >= 0 for item in spending)
    assert all(item["transaction_count"] > 0 for item in spending)


def test_vendor_totals():
    totals = get_vendor_totals(limit=5)

    assert totals
    assert len(totals) <= 5
    assert all(item["vendor"] is not None for item in totals)
    assert all(float(item["total_spending"]) >= 0 for item in totals)
    assert all(item["transaction_count"] > 0 for item in totals)


def test_revenue_analysis():
    analysis = get_revenue_analysis(period="month")

    assert analysis["period"] == "month"
    assert float(analysis["total_revenue"]) >= 0
    assert analysis["transaction_count"] >= 0
    assert all(item["period"] for item in analysis["periods"])
    assert all(
        float(item["total_revenue"]) >= 0
        for item in analysis["periods"]
    )


def test_expense_trends():
    trends = get_expense_trends(period="month")

    assert trends["period"] == "month"
    assert float(trends["total_expenses"]) >= 0
    assert trends["transaction_count"] >= 0
    assert all(item["period"] for item in trends["periods"])
    assert all(
        float(item["total_expenses"]) >= 0
        for item in trends["periods"]
    )


def test_customer_metrics():
    metrics = get_customer_metrics()

    assert len(metrics) > 0
    assert metrics[0][0] == 1


def test_financial_summary():
    summary = get_financial_summary()

    assert summary[0] == 6236.8
    assert summary[1] == 3909
    assert summary[2] == 2327.8
    assert summary[3] == 37.32

def test_accounting_insights():
    insights = get_accounting_insights()

    assert len(insights) == 4
    assert insights[0]["type"] == "financial_summary"
    assert insights[1]["type"] == "margin"
    assert insights[2]["type"] == "top_category"
    assert insights[3]["type"] == "bottom_category"


def test_bookkeeping_summary():
    summary = get_bookkeeping_summary()

    assert summary[0] == 950
    assert summary[1] == 228.5
    assert summary[2] == 721.5
    assert summary[3] == 3


def test_transactions_requiring_review():
    transactions = get_transactions_requiring_review()

    assert len(transactions) == 3

    assert transactions[0][0] == 1
    assert transactions[0][7] == "Software"

    assert transactions[1][0] == 4
    assert transactions[1][7] == "Bank Fees"

    assert transactions[2][0] == 5
    assert transactions[2][7] == "Software"

def test_approve_transaction_category():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'CATEGORY_APPROVED'
            """)

            cursor.execute("""
                UPDATE financial_transactions
                SET
                    ai_suggested_category = 'Software',
                    ai_confidence = 0.97,
                    accounting_category_id = NULL,
                    reconciliation_status = 'UNMATCHED'
                WHERE transaction_id = 1
            """)

            connection.commit()
    finally:
        connection.close()

    result = approve_transaction_category(1)

    assert result is True

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    accounting_category_id,
                    reconciliation_status
                FROM financial_transactions
                WHERE transaction_id = 1
            """)

            row = cursor.fetchone()

            assert row[0] == 3
            assert row[1] == "MATCHED"

            cursor.execute("""
                SELECT
                    financial_transaction_id,
                    action,
                    details
                FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'CATEGORY_APPROVED'
                ORDER BY audit_id DESC
                FETCH FIRST 1 ROW ONLY
            """)

            audit_row = cursor.fetchone()

            assert audit_row[0] == 1
            assert audit_row[1] == "CATEGORY_APPROVED"
            assert audit_row[2] == (
                "User approved AI-suggested accounting category."
            )

            cursor.execute("""
                UPDATE financial_transactions
                SET
                    accounting_category_id = NULL,
                    reconciliation_status = 'UNMATCHED'
                WHERE transaction_id = 1
            """)

            cursor.execute("""
                DELETE FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'CATEGORY_APPROVED'
            """)

            connection.commit()
    finally:
        connection.close()


def test_reject_transaction_category():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'CATEGORY_REJECTED'
            """)

            cursor.execute("""
                UPDATE financial_transactions
                SET
                    ai_suggested_category = 'Software',
                    ai_confidence = 0.97
                WHERE transaction_id = 1
            """)

            connection.commit()
    finally:
        connection.close()

    result = reject_transaction_category(1)

    assert result is True

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    ai_suggested_category,
                    ai_confidence
                FROM financial_transactions
                WHERE transaction_id = 1
            """)

            row = cursor.fetchone()

            assert row[0] is None
            assert row[1] is None

            cursor.execute("""
                SELECT
                    financial_transaction_id,
                    action,
                    details
                FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'CATEGORY_REJECTED'
                ORDER BY audit_id DESC
                FETCH FIRST 1 ROW ONLY
            """)

            audit_row = cursor.fetchone()

            assert audit_row[0] == 1
            assert audit_row[1] == "CATEGORY_REJECTED"
            assert audit_row[2] == (
                "User rejected AI-suggested accounting category."
            )

            cursor.execute("""
                DELETE FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'CATEGORY_REJECTED'
            """)

            connection.commit()
    finally:
        connection.close()


def test_bookkeeping_categories():
    categories = get_bookkeeping_categories()

    assert len(categories) == 8

    assert categories[0][0] == 1
    assert categories[0][1] == "4000"
    assert categories[0][2] == "Sales Revenue"
    assert categories[0][3] == "REVENUE"

    assert categories[2][0] == 3
    assert categories[2][1] == "6100"
    assert categories[2][2] == "Software"
    assert categories[2][3] == "EXPENSE"

    assert categories[4][0] == 5
    assert categories[4][1] == "6300"
    assert categories[4][2] == "Bank Fees"
    assert categories[4][3] == "EXPENSE"



def test_assign_transaction_category():
    result = assign_transaction_category(1, 1)

    assert result is True

    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
    accounting_category_id,
    reconciliation_status
                FROM financial_transactions
                WHERE transaction_id = 1
            """)

            row = cursor.fetchone()

            assert row[0] == 1
            assert row[1] == "MATCHED"

            cursor.execute("""
    UPDATE financial_transactions
    SET
        category = NULL,
        accounting_category_id = NULL,
        reconciliation_status = 'UNMATCHED'
    WHERE transaction_id = 1
""")

            connection.commit()
    finally:
        connection.close()


def test_cancel_transaction_rejection():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'REJECTION_CANCELLED'
            """)

            cursor.execute("""
                UPDATE financial_transactions
                SET
                    original_ai_category = 'Software',
                    original_ai_confidence = 0.97,
                    ai_suggested_category = NULL,
                    ai_confidence = NULL
                WHERE transaction_id = 1
            """)

            connection.commit()
    finally:
        connection.close()

    result = cancel_transaction_rejection(1)

    assert result is True

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    ai_suggested_category,
                    ai_confidence
                FROM financial_transactions
                WHERE transaction_id = 1
            """)

            row = cursor.fetchone()

            assert row[0] == "Software"
            assert row[1] == 0.97

            cursor.execute("""
                SELECT
                    financial_transaction_id,
                    action,
                    details
                FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'REJECTION_CANCELLED'
                ORDER BY audit_id DESC
                FETCH FIRST 1 ROW ONLY
            """)

            audit_row = cursor.fetchone()

            assert audit_row[0] == 1
            assert audit_row[1] == "REJECTION_CANCELLED"
            assert audit_row[2] == (
                "User cancelled category rejection and restored AI suggestion."
            )

            cursor.execute("""
                DELETE FROM audit_log
                WHERE financial_transaction_id = 1
                  AND action = 'REJECTION_CANCELLED'
            """)

            connection.commit()
    finally:
        connection.close()


def test_reconcile_bank_transactions():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
    UPDATE bank_transactions
    SET
        status = 'UNMATCHED',
        financial_transaction_id = NULL,
        match_type = NULL,
        match_confidence = NULL,
        investigation_status = NULL
    WHERE bank_transaction_id IN (1, 2, 3, 4)
""")
            

            connection.commit()
    finally:
        connection.close()

    result = run_reconciliation()

    assert result is True

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
    bank_transaction_id,
    status,
    financial_transaction_id,
    match_type,
    match_confidence
                FROM bank_transactions
                WHERE bank_transaction_id IN (1, 2, 3, 4)
                ORDER BY bank_transaction_id
            """)

            rows = cursor.fetchall()

            assert rows[0][0] == 1
            assert rows[0][1] == "MATCHED"
            assert rows[0][2] == 3
            assert rows[0][3] == "EXACT_MATCH"
            assert rows[0][4] == 1

            assert rows[1][0] == 2
            assert rows[1][1] == "MATCHED"
            assert rows[1][2] == 1
            assert rows[1][3] == "EXACT_MATCH"
            assert rows[1][4] == 1

            assert rows[2][0] == 3
            assert rows[2][1] == "UNMATCHED"
            assert rows[2][2] is None
            assert rows[2][3] == "NO_MATCH"
            assert rows[2][4] == 0

            assert rows[3][0] == 4
            assert rows[3][1] == "UNMATCHED"
            assert rows[3][2] == 5
            assert rows[3][3] == "POSSIBLE_MATCH"
            assert rows[3][4] == 0.9

            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL
                WHERE bank_transaction_id IN (1, 2, 3, 4)
            """)

            connection.commit()
    finally:
        connection.close()


def test_reconciliation_review_queue():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL,
                    match_type = NULL,
                    match_confidence = NULL
                WHERE bank_transaction_id IN (1, 2, 3, 4)
            """)

            connection.commit()
    finally:
        connection.close()

    result = run_reconciliation()

    assert result is True

    rows = get_reconciliation_review_queue()

    assert len(rows) == 2

    rows_by_match_type = {
        row[6]: row
        for row in rows
    }

    possible_match = rows_by_match_type["POSSIBLE_MATCH"]

    assert possible_match[0] == 4
    assert possible_match[4] == "UNMATCHED"
    assert possible_match[5] == 5
    assert possible_match[6] == "POSSIBLE_MATCH"
    assert possible_match[7] == 0.9
    assert possible_match[9] == "Microsoft 365"

    no_match = rows_by_match_type["NO_MATCH"]

    assert no_match[0] == 3
    assert no_match[4] == "UNMATCHED"
    assert no_match[5] is None
    assert no_match[6] == "NO_MATCH"
    assert no_match[7] == 0
    assert no_match[9] is None

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL,
                    match_type = NULL,
                    match_confidence = NULL
                WHERE bank_transaction_id IN (1, 2, 3, 4)
            """)

            connection.commit()
    finally:
        connection.close()


def test_reject_bank_transaction_match():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM audit_log
                WHERE bank_transaction_id = 4
                  AND action = 'RECONCILIATION_REJECTED'
            """)

            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = 5,
                    match_type = 'POSSIBLE_MATCH',
                    match_confidence = 0.90,
                    investigation_status = NULL
                WHERE bank_transaction_id = 4
            """)

            connection.commit()
    finally:
        connection.close()

    result = reject_bank_transaction_match(4)

    assert result is True

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    status,
                    financial_transaction_id,
                    match_type,
                    match_confidence
                FROM bank_transactions
                WHERE bank_transaction_id = 4
            """)

            row = cursor.fetchone()

            assert row[0] == "UNMATCHED"
            assert row[1] is None
            assert row[2] == "NO_MATCH"
            assert row[3] == 0

            cursor.execute("""
                SELECT
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details
                FROM audit_log
                WHERE bank_transaction_id = 4
                  AND action = 'RECONCILIATION_REJECTED'
                ORDER BY audit_id DESC
                FETCH FIRST 1 ROW ONLY
            """)

            audit_row = cursor.fetchone()

            assert audit_row[0] == 4
            assert audit_row[1] is None
            assert audit_row[2] == "RECONCILIATION_REJECTED"
            assert audit_row[3] == (
                "User rejected possible reconciliation match."
            )

            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL,
                    match_type = NULL,
                    match_confidence = NULL,
                    investigation_status = NULL
                WHERE bank_transaction_id = 4
            """)

            cursor.execute("""
                DELETE FROM audit_log
                WHERE bank_transaction_id = 4
                  AND action = 'RECONCILIATION_REJECTED'
            """)

            connection.commit()
    finally:
        connection.close()


def test_confirm_bank_transaction_match():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM audit_log
                WHERE bank_transaction_id = 4
                  AND action = 'RECONCILIATION_CONFIRMED'
            """)

            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = 5,
                    match_type = 'POSSIBLE_MATCH',
                    match_confidence = 0.90,
                    investigation_status = NULL
                WHERE bank_transaction_id = 4
            """)

            connection.commit()
    finally:
        connection.close()

    result = confirm_bank_transaction_match(4)

    assert result is True

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    status,
                    financial_transaction_id,
                    match_type,
                    match_confidence
                FROM bank_transactions
                WHERE bank_transaction_id = 4
            """)

            row = cursor.fetchone()

            assert row[0] == "MATCHED"
            assert row[1] == 5
            assert row[2] == "POSSIBLE_MATCH"
            assert row[3] == 0.90

            cursor.execute("""
                SELECT
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details
                FROM audit_log
                WHERE bank_transaction_id = 4
                  AND action = 'RECONCILIATION_CONFIRMED'
                ORDER BY audit_id DESC
                FETCH FIRST 1 ROW ONLY
            """)

            audit_row = cursor.fetchone()

            assert audit_row[0] == 4
            assert audit_row[1] == 5
            assert audit_row[2] == "RECONCILIATION_CONFIRMED"
            assert audit_row[3] == (
                "User confirmed possible reconciliation match."
            )

            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL,
                    match_type = NULL,
                    match_confidence = NULL,
                    investigation_status = NULL
                WHERE bank_transaction_id = 4
            """)

            cursor.execute("""
                DELETE FROM audit_log
                WHERE bank_transaction_id = 4
                  AND action = 'RECONCILIATION_CONFIRMED'
            """)

            connection.commit()
    finally:
        connection.close()


def test_investigate_bank_transaction():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM audit_log
                WHERE bank_transaction_id = 3
                  AND action = 'TRANSACTION_INVESTIGATED'
            """)

            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL,
                    match_type = 'NO_MATCH',
                    match_confidence = 0,
                    investigation_status = NULL
                WHERE bank_transaction_id = 3
            """)

            connection.commit()
    finally:
        connection.close()

    result = investigate_bank_transaction(3)

    assert result is True

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    status,
                    match_type,
                    investigation_status
                FROM bank_transactions
                WHERE bank_transaction_id = 3
            """)

            row = cursor.fetchone()

            assert row[0] == "UNMATCHED"
            assert row[1] == "NO_MATCH"
            assert row[2] == "INVESTIGATED"

            cursor.execute("""
                SELECT
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details
                FROM audit_log
                WHERE bank_transaction_id = 3
                  AND action = 'TRANSACTION_INVESTIGATED'
                ORDER BY audit_id DESC
                FETCH FIRST 1 ROW ONLY
            """)

            audit_row = cursor.fetchone()

            assert audit_row[0] == 3
            assert audit_row[1] is None
            assert audit_row[2] == "TRANSACTION_INVESTIGATED"
            assert audit_row[3] == (
                "User marked unmatched bank transaction as investigated."
            )

            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL,
                    match_type = NULL,
                    match_confidence = NULL,
                    investigation_status = NULL
                WHERE bank_transaction_id = 3
            """)

            cursor.execute("""
                DELETE FROM audit_log
                WHERE bank_transaction_id = 3
                  AND action = 'TRANSACTION_INVESTIGATED'
            """)

            connection.commit()
    finally:
        connection.close()


def test_log_audit_event():
    result = log_audit_event(
        action="TEST_AUDIT",
        bank_transaction_id=3,
        details="Test audit event",
    )

    assert result is True

    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    bank_transaction_id,
                    financial_transaction_id,
                    action,
                    details
                FROM audit_log
                WHERE action = 'TEST_AUDIT'
                ORDER BY audit_id DESC
                FETCH FIRST 1 ROW ONLY
            """)

            row = cursor.fetchone()

            assert row[0] == 3
            assert row[1] is None
            assert row[2] == "TEST_AUDIT"
            assert row[3] == "Test audit event"

            cursor.execute("""
                DELETE FROM audit_log
                WHERE action = 'TEST_AUDIT'
            """)

            connection.commit()
    finally:
        connection.close()


def test_get_audit_log():
    from database import get_connection

    result = log_audit_event(
        action="TEST_AUDIT_QUERY",
        bank_transaction_id=3,
        details="Test audit query event",
    )

    assert result is True

    rows = get_audit_log()

    assert len(rows) >= 1

    latest = rows[0]

    assert latest[1] == 3
    assert latest[2] is None
    assert latest[3] == "TEST_AUDIT_QUERY"
    assert latest[4] == "Test audit query event"
    assert latest[5] is not None

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM audit_log
                WHERE action = 'TEST_AUDIT_QUERY'
            """)

            connection.commit()
    finally:
        connection.close()


class MockResponse:
    output_text = '{"category": "Software", "confidence": 0.97}'


class MockResponses:
    def create(self, **kwargs):
        return MockResponse()


class MockClient:
    def __init__(self):
        self.responses = MockResponses()


def test_suggest_transaction_category():
    suggestion = suggest_transaction_category(
        description="AWS monthly service",
        vendor="Amazon Web Services",
        amount=-129,
        client=MockClient(),
    )

    assert suggestion.category == "Software"
    assert suggestion.confidence == 0.97
    assert suggestion.high_confidence is True

def test_categorize_transaction_with_llm():
    from database import get_connection

    class MockResponse:
        output_text = '{"category": "Software", "confidence": 0.92}'

    class MockResponses:
        def create(self, **kwargs):
            return MockResponse()

    class MockClient:
        def __init__(self):
            self.responses = MockResponses()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    ai_suggested_category,
                    ai_confidence
                FROM financial_transactions
                WHERE transaction_id = 2
            """)

            original_row = cursor.fetchone()

            original_category = original_row[0]
            original_confidence = original_row[1]
    finally:
        connection.close()

    result = categorize_transaction_with_llm(
        transaction_id=2,
        client=MockClient(),
    )

    assert result.category == "Software"
    assert result.confidence == 0.92

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    ai_suggested_category,
                    ai_confidence
                FROM financial_transactions
                WHERE transaction_id = 2
            """)

            row = cursor.fetchone()

            assert row[0] == "Software"
            assert row[1] == 0.92

            cursor.execute("""
                UPDATE financial_transactions
                SET
                    ai_suggested_category = :category,
                    ai_confidence = :confidence
                WHERE transaction_id = 2
            """, {
                "category": original_category,
                "confidence": original_confidence,
            })

            connection.commit()
    finally:
        connection.close()

def test_categorize_uncategorized_transactions():
    from database import get_connection

    class MockResponse:
        output_text = '{"category": "Office Supplies", "confidence": 0.88}'

    class MockResponses:
        def create(self, **kwargs):
            return MockResponse()

    class MockClient:
        def __init__(self):
            self.responses = MockResponses()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    transaction_id,
                    category,
                    ai_suggested_category,
                    ai_confidence
                FROM financial_transactions
                WHERE transaction_id IN (2, 3)
                ORDER BY transaction_id
            """)

            original_rows = cursor.fetchall()

            cursor.execute("""
                UPDATE financial_transactions
                SET
                    category = NULL,
                    ai_suggested_category = NULL,
                    ai_confidence = NULL
                WHERE transaction_id IN (2, 3)
            """)

            connection.commit()
    finally:
        connection.close()

    results = categorize_uncategorized_transactions(
        client=MockClient(),
    )

    transaction_ids = {
        item["transaction_id"]
        for item in results
    }

    assert 2 in transaction_ids
    assert 3 in transaction_ids

    for item in results:
        assert item["category"] == "Office Supplies"
        assert item["confidence"] == 0.88

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            for transaction_id, category, ai_category, ai_confidence in original_rows:
                cursor.execute("""
                    UPDATE financial_transactions
                    SET
                        category = :category,
                        ai_suggested_category = :ai_category,
                        ai_confidence = :ai_confidence
                    WHERE transaction_id = :transaction_id
                """, {
                    "category": category,
                    "ai_category": ai_category,
                    "ai_confidence": ai_confidence,
                    "transaction_id": transaction_id,
                })

            connection.commit()
    finally:
        connection.close()


def test_categorize_uncategorized_transactions_skips_categorized_transaction():
    from database import get_connection

    class MockResponse:
        output_text = '{"category": "Advertising", "confidence": 0.91}'

    class MockResponses:
        def create(self, **kwargs):
            raise AssertionError(
                "Categorized transaction should not be sent to the AI."
            )

    class MockClient:
        def __init__(self):
            self.responses = MockResponses()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    category,
                    ai_suggested_category,
                    ai_confidence
                FROM financial_transactions
                WHERE transaction_id = 3
            """)

            original_row = cursor.fetchone()
    finally:
        connection.close()

    result = categorize_uncategorized_transactions(
        client=MockClient(),
    )

    transaction_ids = {
        item["transaction_id"]
        for item in result
    }

    assert 3 not in transaction_ids

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    category,
                    ai_suggested_category,
                    ai_confidence
                FROM financial_transactions
                WHERE transaction_id = 3
            """)

            row = cursor.fetchone()

            assert row[0] == original_row[0]
            assert row[1] == original_row[1]
            assert row[2] == original_row[2]
    finally:
        connection.close()


def test_is_high_confidence_suggestion():
    high_confidence = CategorySuggestion(
        category="Software",
        confidence=0.80,
    )

    low_confidence = CategorySuggestion(
        category="Uncategorized",
        confidence=0.79,
    )

    assert AI_CONFIDENCE_THRESHOLD == 0.80
    assert is_high_confidence_suggestion(high_confidence) is True
    assert is_high_confidence_suggestion(low_confidence) is False


def test_category_suggestion_confidence_status():
    high = CategorySuggestion(
        category="Software",
        confidence=0.80,
    )

    low = CategorySuggestion(
        category="Uncategorized",
        confidence=0.00,
    )

    assert high.high_confidence is True
    assert low.high_confidence is False


def test_get_accounting_context():
    from accounting_rag import get_accounting_context

    context = get_accounting_context(
        description="Microsoft 365 subscription",
        vendor="Microsoft",
    )

    assert len(context.categories) > 0

    category_names = {
        category["account_name"]
        for category in context.categories
    }

    assert "Software" in category_names

    for example in context.examples:
        assert example["category"] is not None


def test_suggest_transaction_category_includes_rag_context():
    from accounting_rag import AccountingContext
    from llm_categorizer import suggest_transaction_category

    captured = {}

    class MockResponse:
        output_text = '{"category": "Office Supplies", "confidence": 0.88}'

    class MockResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return MockResponse()

    class MockClient:
        def __init__(self):
            self.responses = MockResponses()

    context = AccountingContext(
        categories=[
            {
                "category_id": 4,
                "account_code": "6200",
                "account_name": "Office Supplies",
                "account_type": "EXPENSE",
            }
        ],
        examples=[
            {
                "transaction_id": 2,
                "description": "Office supplies",
                "vendor": "Office Depot",
                "category": "Office Supplies",
            }
        ],
    )

    suggestion = suggest_transaction_category(
        description="Printer paper",
        vendor="Office Depot",
        amount=-25,
        client=MockClient(),
        context=context,
    )

    assert suggestion.category == "Office Supplies"
    assert suggestion.confidence == 0.88

    messages = captured["input"]

    system_message = messages[0]["content"]
    user_message = messages[1]["content"]

    assert "6200 Office Supplies (EXPENSE)" in user_message
    assert "Office supplies (Office Depot) -> Office Supplies" in user_message
    assert "Office Depot" in user_message
    assert system_message is not None


def test_validate_category_suggestion_accepts_valid_category():
    from accounting_rag import AccountingContext
    from llm_categorizer import (
        CategorySuggestion,
        validate_category_suggestion,
    )

    context = AccountingContext(
        categories=[
            {
                "category_id": 3,
                "account_code": "6100",
                "account_name": "Software",
                "account_type": "EXPENSE",
            },
            {
                "category_id": 4,
                "account_code": "6200",
                "account_name": "Office Supplies",
                "account_type": "EXPENSE",
            },
        ],
        examples=[],
    )

    suggestion = CategorySuggestion(
        category="Software",
        confidence=0.95,
    )

    result = validate_category_suggestion(
        suggestion,
        context,
    )

    assert result.category == "Software"
    assert result.confidence == 0.95


def test_validate_category_suggestion_rejects_invalid_category():
    import pytest

    from accounting_rag import AccountingContext
    from llm_categorizer import (
        CategorySuggestion,
        validate_category_suggestion,
    )

    context = AccountingContext(
        categories=[
            {
                "category_id": 3,
                "account_code": "6100",
                "account_name": "Software",
                "account_type": "EXPENSE",
            }
        ],
        examples=[],
    )

    suggestion = CategorySuggestion(
        category="Marketing",
        confidence=0.99,
    )

    with pytest.raises(
        ValueError,
        match="Invalid accounting category returned by AI",
    ):
        validate_category_suggestion(
            suggestion,
            context,
        )


def test_low_confidence_suggestion_requires_review():
    from llm_categorizer import CategorySuggestion

    suggestion = CategorySuggestion(
        category="Software",
        confidence=0.10,
    )

    assert suggestion.high_confidence is False


def test_validate_category_suggestion_rejects_uncategorized():
    from accounting_rag import AccountingContext
    from llm_categorizer import (
        CategorySuggestion,
        validate_category_suggestion,
    )

    context = AccountingContext(
        categories=[
            {
                "category_id": 3,
                "account_code": "6100",
                "account_name": "Software",
                "account_type": "EXPENSE",
            },
            {
                "category_id": 4,
                "account_code": "6200",
                "account_name": "Office Supplies",
                "account_type": "EXPENSE",
            },
        ],
        examples=[],
    )

    suggestion = CategorySuggestion(
        category="Uncategorized",
        confidence=0.99,
    )

    import pytest

    with pytest.raises(
        ValueError,
        match="Invalid accounting category returned by AI",
    ):
        validate_category_suggestion(
            suggestion,
            context,
        )


def test_ai_tool_registry():
    from ai_tools import TOOL_REGISTRY

    assert "get_bookkeeping_summary" in TOOL_REGISTRY
    assert "get_ai_review_queue" in TOOL_REGISTRY
    assert "investigate_uncategorized_transaction" in TOOL_REGISTRY
    assert "get_reconciliation_review" in TOOL_REGISTRY
    assert "investigate_reconciliation_issue" in TOOL_REGISTRY
    assert "get_audit_log" in TOOL_REGISTRY
    assert "get_spending_by_category" in TOOL_REGISTRY
    assert "get_vendor_totals" in TOOL_REGISTRY
    assert "get_revenue_analysis" in TOOL_REGISTRY
    assert "get_expense_trends" in TOOL_REGISTRY
    assert "get_financial_statistics" in TOOL_REGISTRY
    assert "get_financial_anomalies" in TOOL_REGISTRY

    assert callable(TOOL_REGISTRY["get_bookkeeping_summary"])
    assert callable(TOOL_REGISTRY["get_ai_review_queue"])
    assert callable(
        TOOL_REGISTRY["investigate_uncategorized_transaction"]
    )
    assert callable(TOOL_REGISTRY["get_reconciliation_review"])
    assert callable(
        TOOL_REGISTRY["investigate_reconciliation_issue"]
    )
    assert callable(TOOL_REGISTRY["get_audit_log"])
    assert callable(TOOL_REGISTRY["get_spending_by_category"])
    assert callable(TOOL_REGISTRY["get_vendor_totals"])
    assert callable(TOOL_REGISTRY["get_revenue_analysis"])
    assert callable(TOOL_REGISTRY["get_expense_trends"])
    assert callable(TOOL_REGISTRY["get_financial_statistics"])
    assert callable(TOOL_REGISTRY["get_financial_anomalies"])


def test_ai_tool_definitions():
    from ai_tools import TOOL_DEFINITIONS

    names = {
        tool["name"]
        for tool in TOOL_DEFINITIONS
    }

    assert names == {
        "get_bookkeeping_summary",
        "get_ai_review_queue",
        "investigate_uncategorized_transaction",
        "get_reconciliation_review",
        "investigate_reconciliation_issue",
        "get_audit_log",
        "get_spending_by_category",
        "get_vendor_totals",
        "get_revenue_analysis",
        "get_expense_trends",
        "get_financial_statistics",
        "get_financial_anomalies",
        "get_transactions_by_date",
        "get_transactions",
    }

    assert "get_transactions" in names

    transaction_tool = next(
        tool
        for tool in TOOL_DEFINITIONS
        if tool["name"] == "get_transactions"
    )

    assert transaction_tool["type"] == "function"
    expected_filters = {
        "category",
        "vendor",
        "transaction_type",
        "reconciliation_status",
        "categorization_state",
        "min_ai_confidence",
        "max_ai_confidence",
        "min_amount",
        "max_amount",
        "status",
        "start_date",
        "end_date",
    }
    assert set(
        transaction_tool["parameters"]["properties"]
    ) == expected_filters
    assert set(
        transaction_tool["parameters"]["required"]
    ) == expected_filters

    category_spending_tool = next(
        tool
        for tool in TOOL_DEFINITIONS
        if tool["name"] == "get_spending_by_category"
    )
    assert set(category_spending_tool["parameters"]["properties"]) == {
        "category",
        "start_date",
        "end_date",
    }
    assert set(category_spending_tool["parameters"]["required"]) == {
        "category",
        "start_date",
        "end_date",
    }

    vendor_totals_tool = next(
        tool
        for tool in TOOL_DEFINITIONS
        if tool["name"] == "get_vendor_totals"
    )
    assert set(vendor_totals_tool["parameters"]["properties"]) == {
        "vendor",
        "start_date",
        "end_date",
        "limit",
    }
    assert set(vendor_totals_tool["parameters"]["required"]) == {
        "vendor",
        "start_date",
        "end_date",
        "limit",
    }

    revenue_tool = next(
        tool
        for tool in TOOL_DEFINITIONS
        if tool["name"] == "get_revenue_analysis"
    )
    assert set(revenue_tool["parameters"]["properties"]) == {
        "start_date",
        "end_date",
        "period",
    }
    assert revenue_tool["parameters"]["properties"]["period"]["enum"] == [
        "month",
        "year",
    ]

    expense_trends_tool = next(
        tool
        for tool in TOOL_DEFINITIONS
        if tool["name"] == "get_expense_trends"
    )
    assert set(expense_trends_tool["parameters"]["properties"]) == {
        "category",
        "vendor",
        "start_date",
        "end_date",
        "period",
    }
    assert expense_trends_tool["parameters"]["properties"]["period"]["enum"] == [
        "month",
        "year",
    ]

    for tool in TOOL_DEFINITIONS:
        assert tool["type"] == "function"
        assert tool["description"]
        assert tool["parameters"]["type"] == "object"
        assert tool["parameters"]["additionalProperties"] is False

def test_ai_assistant_selects_bookkeeping_summary():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "What's our bookkeeping summary?"
    )

    assert response.tool_name == "get_bookkeeping_summary"
    assert response.tool_result is not None


def test_ai_assistant_selects_ai_review_queue():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Which transactions need AI review?"
    )

    assert response.tool_name == "get_ai_review_queue"
    assert response.tool_result is not None


def test_ai_assistant_selects_reconciliation_review():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Are there any unmatched reconciliation issues?"
    )

    assert response.tool_name == "get_reconciliation_review"
    assert response.tool_result is not None


def test_ai_assistant_selects_audit_log():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Show me recent audit activity."
    )

    assert response.tool_name == "get_audit_log"
    assert response.tool_result is not None


def test_ai_assistant_handles_unknown_question():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "What's the weather today?"
    )

    assert response.tool_name is None
    assert response.tool_result is None


def test_ai_assistant_formats_bookkeeping_summary():
    from ai_assistant import _format_bookkeeping_summary

    result = (
        950.0,
        228.5,
        721.5,
        3,
    )

    message = _format_bookkeeping_summary(result)

    assert "revenue €950.00" in message
    assert "expenses €228.50" in message
    assert "net movement €721.50" in message
    assert "3 transactions requiring review" in message


def test_ai_assistant_formats_ai_review_queue():
    from ai_assistant import _format_ai_review_queue

    result = [
        (
            1,
            "2026-08-01",
            "EXPENSE",
            "Amazon Web Services",
            -129.0,
            None,
            "Amazon Web Services",
            "Software",
            0.97,
            "UNMATCHED",
            "POSTED",
            "HIGH_CONFIDENCE",
        )
    ]

    message = _format_ai_review_queue(result)

    assert "1 transaction(s) require AI categorization review" in message
    assert "Transaction 1" in message
    assert "Amazon Web Services" in message
    assert "AI suggestion: Software" in message
    assert "confidence: 97%" in message


def test_ai_assistant_formats_reconciliation_review():
    from ai_assistant import _format_reconciliation_review

    result = [
        (
            10,
            "2026-08-15",
            "AWS payment",
            -129.0,
            "UNMATCHED",
            1,
            "POSSIBLE_MATCH",
            0.84,
            "2026-08-01",
            "Amazon Web Services",
            -129.0,
        )
    ]

    message = _format_reconciliation_review(result)

    assert "1 reconciliation item(s) require review" in message
    assert "Bank transaction 10" in message
    assert "AWS payment" in message
    assert "amount €-129.00" in message
    assert "status: UNMATCHED" in message
    assert "match type: POSSIBLE_MATCH" in message
    assert "confidence: 84%" in message


def test_ai_assistant_formats_audit_log():
    from ai_assistant import _format_audit_log

    result = [
        (
            15,
            None,
            1,
            "CATEGORY_APPROVED",
            "User approved AI-suggested accounting category.",
            "2026-09-01 13:22:11",
        )
    ]

    message = _format_audit_log(result)

    assert "1 recent audit log entry:" in message
    assert "Audit 15" in message
    assert "CATEGORY_APPROVED" in message
    assert "User approved AI-suggested accounting category." in message

def test_ai_assistant_openai_executes_tool_call():
    from ai_assistant import ask_assistant_openai

    class ToolCall:
        type = "function_call"
        name = "get_bookkeeping_summary"
        arguments = "{}"
        call_id = "call_123"

    class FirstResponse:
        id = "resp_123"
        output = [ToolCall()]
        output_text = ""

    class FinalResponse:
        output_text = (
            "Your bookkeeping summary shows revenue of €950.00 "
            "and expenses of €228.50."
        )

    class MockResponses:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                return FirstResponse()

            return FinalResponse()


    class MockClient:
        def __init__(self):
            self.responses = MockResponses()

    client = MockClient()

    result = ask_assistant_openai(
        "What's our bookkeeping summary?",
        client=client,
    )

    assert result.tool_name == "get_bookkeeping_summary"
    assert result.tool_result is not None
    assert "€950.00" in result.message
    assert "€228.50" in result.message

    assert len(client.responses.calls) == 2

    second_call = client.responses.calls[1]

    assert second_call["previous_response_id"] == "resp_123"

    tool_output = second_call["input"][0]

    assert tool_output["type"] == "function_call_output"
    assert tool_output["call_id"] == "call_123"

def test_ai_assistant_defaults_to_demo_mode(monkeypatch):
    from ai_assistant import ask_assistant

    monkeypatch.delenv(
        "AI_ASSISTANT_MODE",
        raising=False,
    )

    response = ask_assistant(
        "What's our bookkeeping summary?"
    )

    assert response.tool_name == "get_bookkeeping_summary"
    assert response.tool_result is not None
    assert "bookkeeping summary" in response.message.lower()


def test_ai_assistant_openai_mode(monkeypatch):
    import ai_assistant

    monkeypatch.setenv(
        "AI_ASSISTANT_MODE",
        "openai",
    )

    expected = ai_assistant.AssistantResponse(
        message="Mock OpenAI response",
        tool_name="get_bookkeeping_summary",
        tool_result={"test": True},
    )

    def mock_openai(question):
        assert question == "What's our bookkeeping summary?"
        return expected

    monkeypatch.setattr(
        ai_assistant,
        "ask_assistant_openai",
        mock_openai,
    )

    response = ai_assistant.ask_assistant(
        "What's our bookkeeping summary?"
    )

    assert response is expected


def test_ai_assistant_rejects_invalid_mode(monkeypatch):
    import pytest

    from ai_assistant import ask_assistant

    monkeypatch.setenv(
        "AI_ASSISTANT_MODE",
        "invalid",
    )

    with pytest.raises(
        ValueError,
        match="AI_ASSISTANT_MODE must be 'demo' or 'openai'",
    ):
        ask_assistant(
            "What's our bookkeeping summary?"
        )


def test_ai_assistant_handles_multiple_tools():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Give me the bookkeeping summary and "
        "tell me if there are any reconciliation issues."
    )

    assert response.tool_name is not None
    assert "get_bookkeeping_summary" in response.tool_name
    assert "get_reconciliation_review" in response.tool_name

    assert isinstance(response.tool_result, list)
    assert len(response.tool_result) == 2

    assert "bookkeeping summary" in response.message.lower()
    assert "reconciliation" in response.message.lower()



def test_ai_assistant_handles_ai_review_and_audit():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Show me AI review items and recent audit activity."
    )

    assert "get_ai_review_queue" in response.tool_name
    assert "get_audit_log" in response.tool_name

    assert isinstance(response.tool_result, list)
    assert len(response.tool_result) == 2

def test_tool_get_transactions_by_date():
    from ai_tools import tool_get_transactions_by_date

    result = tool_get_transactions_by_date(
        start_date="2026-08-01",
        end_date="2026-08-10",
    )

    assert isinstance(result, list)
    assert len(result) > 0

    for transaction in result:
        assert "transaction_id" in transaction
        assert "transaction_date" in transaction
        assert "description" in transaction
        assert "amount" in transaction

def test_transactions_by_date_tool_definition():
    from ai_tools import TOOL_DEFINITIONS, TOOL_REGISTRY

    assert "get_transactions_by_date" in TOOL_REGISTRY
    assert callable(
        TOOL_REGISTRY["get_transactions_by_date"]
    )

    definition = next(
        tool
        for tool in TOOL_DEFINITIONS
        if tool["name"] == "get_transactions_by_date"
    )

    assert definition["type"] == "function"
    assert definition["parameters"]["properties"][
        "start_date"
    ]["type"] == "string"
    assert definition["parameters"]["properties"][
        "end_date"
    ]["type"] == "string"
    assert definition["parameters"]["required"] == [
        "start_date",
        "end_date",
    ]

def test_ai_assistant_selects_transactions_by_date_tool():
    from ai_assistant import _select_tools

    tools = _select_tools(
        "Show me transactions from 2026-08-01 to 2026-08-10."
    )

    assert "get_transactions_by_date" in tools


def test_extract_date_range():
    from ai_assistant import _extract_date_range

    result = _extract_date_range(
        "Show me transactions from 2026-08-01 to 2026-08-10."
    )

    assert result == (
        "2026-08-01",
        "2026-08-10",
    )


def test_ai_assistant_get_transactions_by_date():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Show me transactions from "
        "2026-08-01 to 2026-08-10."
    )

    assert response.tool_name == "get_transactions_by_date"
    assert isinstance(response.tool_result, list)
    assert len(response.tool_result) > 0

    assert "transaction(s) found" in response.message


def test_extract_date_range_returns_none_when_dates_are_missing():
    from ai_assistant import _extract_date_range

    assert _extract_date_range(
        "Show me transactions."
    ) is None


def test_execute_tool_without_arguments():
    from ai_assistant import _execute_tool

    result = _execute_tool(
        "get_bookkeeping_summary"
    )

    assert result is not None


def test_execute_tool_with_arguments():
    from ai_assistant import _execute_tool

    result = _execute_tool(
        "get_transactions_by_date",
        {
            "start_date": "2026-08-01",
            "end_date": "2026-08-10",
        },
    )

    assert isinstance(result, list)


def test_execute_tool_rejects_unknown_tool():
    import pytest

    from ai_assistant import _execute_tool

    with pytest.raises(
        ValueError,
        match="Unknown AI tool requested",
    ):
        _execute_tool("does_not_exist")


def test_tool_get_transactions_with_filters():
    from ai_tools import tool_get_transactions

    result = tool_get_transactions(
        category="Software",
        min_amount=50,
    )

    assert isinstance(result, list)

    for transaction in result:
        assert transaction["category"] == "Software"
        assert abs(float(transaction["amount"])) >= 50


def test_tool_get_transactions_filters_by_status():
    from ai_tools import tool_get_transactions

    result = tool_get_transactions(
        status="PENDING",
    )

    assert isinstance(result, list)

    for transaction in result:
        assert transaction["status"] == "PENDING"


def test_tool_get_transactions_filters_by_vendor():
    from ai_tools import tool_get_transactions

    result = tool_get_transactions(
        vendor="microsoft",
    )

    assert result

    for transaction in result:
        assert "microsoft" in transaction["vendor"].lower()


def test_tool_get_transactions_filters_by_transaction_type():
    from ai_tools import tool_get_transactions

    result = tool_get_transactions(
        transaction_type="EXPENSE",
    )

    assert result

    for transaction in result:
        assert transaction["transaction_type"] == "EXPENSE"


def test_tool_get_transactions_filters_by_reconciliation_status():
    from ai_tools import tool_get_transactions

    result = tool_get_transactions(
        reconciliation_status="UNMATCHED",
    )

    assert result

    for transaction in result:
        assert transaction["reconciliation_status"] == "UNMATCHED"


def test_tool_get_transactions_filters_by_categorization_state():
    from ai_tools import tool_get_transactions

    result = tool_get_transactions(
        categorization_state="UNCATEGORIZED",
    )

    assert result

    for transaction in result:
        assert transaction["category"] is None


def test_tool_get_transactions_filters_by_ai_confidence():
    from ai_tools import tool_get_transactions

    result = tool_get_transactions(
        min_ai_confidence=0.80,
    )

    assert result

    for transaction in result:
        assert transaction["ai_confidence"] is not None
        assert float(transaction["ai_confidence"]) >= 0.80


def test_tool_get_transactions_combines_and_binds_optional_filters(monkeypatch):
    import re

    import ai_tools

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, parameters):
            captured["statement"] = statement
            captured["parameters"] = parameters

        def fetchall(self):
            return []

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(
        ai_tools,
        "get_connection",
        lambda: FakeConnection(),
    )

    result = ai_tools.tool_get_transactions(
        category="Software",
        vendor="office depot",
        transaction_type="EXPENSE",
        reconciliation_status="MATCHED",
        categorization_state="CATEGORIZED",
        min_ai_confidence=0.80,
        max_ai_confidence=0.95,
        min_amount=50,
        max_amount=200,
        status="POSTED",
        start_date="2026-08-01",
        end_date="2026-08-31",
    )

    assert result == []
    bind_names = set(
        re.findall(r":([a-z_]+)", captured["statement"])
    )
    assert bind_names == set(captured["parameters"])
    assert captured["parameters"] == {
        "category": "Software",
        "vendor": "office depot",
        "transaction_type": "EXPENSE",
        "reconciliation_status": "MATCHED",
        "categorization_state": "CATEGORIZED",
        "min_ai_confidence": 0.80,
        "max_ai_confidence": 0.95,
        "min_amount": 50,
        "max_amount": 200,
        "status": "POSTED",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
    }

    for value in (
        "Software",
        "office depot",
        "EXPENSE",
        "MATCHED",
        "POSTED",
        "2026-08-01",
        "2026-08-31",
    ):
        assert value not in captured["statement"]

    assert captured["closed"] is True


def test_tool_get_transactions_combines_vendor_with_existing_filters():
    from ai_tools import tool_get_transactions

    result = tool_get_transactions(
        category="Office Supplies",
        vendor="office depot",
        transaction_type="EXPENSE",
        reconciliation_status="MATCHED",
        categorization_state="CATEGORIZED",
        min_amount=80,
        max_amount=90,
        status="POSTED",
        start_date="2026-08-01",
        end_date="2026-08-31",
    )

    assert result

    for transaction in result:
        assert transaction["category"] == "Office Supplies"
        assert "office depot" in transaction["vendor"].lower()
        assert transaction["transaction_type"] == "EXPENSE"
        assert transaction["reconciliation_status"] == "MATCHED"
        assert transaction["category"] is not None
        assert 80 <= abs(float(transaction["amount"])) <= 90
        assert transaction["status"] == "POSTED"


def test_extract_transaction_filters():
    from ai_assistant import _extract_transaction_filters

    result = _extract_transaction_filters(
        "Show me Software expenses over €50"
    )

    assert result == {
        "category": "Software",
        "vendor": None,
        "transaction_type": "EXPENSE",
        "reconciliation_status": None,
        "categorization_state": None,
        "min_ai_confidence": None,
        "max_ai_confidence": None,
        "min_amount": 50.0,
        "max_amount": None,
        "status": None,
        "start_date": None,
        "end_date": None,
    }


def test_extract_transaction_filters_with_status():
    from ai_assistant import _extract_transaction_filters

    result = _extract_transaction_filters(
        "Show me pending Software transactions under €100"
    )

    assert result["category"] == "Software"
    assert result["max_amount"] == 100.0
    assert result["status"] == "PENDING"


def test_extract_transaction_filters_with_vendor():
    from ai_assistant import _extract_transaction_filters

    result = _extract_transaction_filters(
        "Show me Microsoft transactions."
    )

    assert result["vendor"] == "Microsoft"


def test_extract_transaction_filters_with_transaction_types():
    from ai_assistant import _extract_transaction_filters

    examples = {
        "Show me sale transactions.": "SALE",
        "Show me expense transactions.": "EXPENSE",
        "Show me posted bank fees.": "BANK_FEE",
    }

    for question, expected_type in examples.items():
        result = _extract_transaction_filters(question)
        assert result["transaction_type"] == expected_type


def test_extract_transaction_filters_with_reconciliation_statuses():
    from ai_assistant import _extract_transaction_filters

    unmatched = _extract_transaction_filters(
        "Show me unmatched Software transactions."
    )
    matched = _extract_transaction_filters(
        "Show me matched sale transactions."
    )

    assert unmatched["reconciliation_status"] == "UNMATCHED"
    assert matched["reconciliation_status"] == "MATCHED"


def test_extract_transaction_filters_with_categorization_states():
    from ai_assistant import _extract_transaction_filters

    uncategorized = _extract_transaction_filters(
        "Show me uncategorized transactions."
    )
    categorized = _extract_transaction_filters(
        "Show me categorized Microsoft expenses."
    )

    assert uncategorized["categorization_state"] == "UNCATEGORIZED"
    assert categorized["categorization_state"] == "CATEGORIZED"


def test_extract_transaction_filters_with_ai_confidence():
    from ai_assistant import _extract_transaction_filters

    below = _extract_transaction_filters(
        "Show me AI suggestions below 80% confidence."
    )
    high = _extract_transaction_filters(
        "Show me high-confidence uncategorized transactions."
    )

    assert below["min_ai_confidence"] is None
    assert below["max_ai_confidence"] == 0.80
    assert high["min_ai_confidence"] == AI_CONFIDENCE_THRESHOLD
    assert high["max_ai_confidence"] is None


def test_demo_assistant_vendor_only_transactions():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Show me Microsoft transactions."
    )

    assert response.tool_name == "get_transactions"
    assert response.tool_result

    transactions = response.tool_result[0]["result"]

    assert transactions
    assert all(
        transaction["vendor"] == "Microsoft"
        for transaction in transactions
    )
    assert "vendor: Microsoft" in response.message


def test_demo_assistant_combines_vendor_with_existing_filters():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Show me posted Office Depot Office Supplies expenses over €80 "
        "between 2026-08-01 and 2026-08-31."
    )

    assert response.tool_name == "get_transactions"

    transactions = response.tool_result[0]["result"]

    assert transactions

    for transaction in transactions:
        assert transaction["vendor"] == "Office Depot"
        assert transaction["category"] == "Office Supplies"
        assert transaction["transaction_type"] == "EXPENSE"
        assert abs(float(transaction["amount"])) >= 80
        assert transaction["status"] == "POSTED"


def test_demo_assistant_filters_by_transaction_type(monkeypatch):
    from ai_assistant import TOOL_REGISTRY, ask_assistant

    captured = {}

    def fake_get_transactions(**arguments):
        captured.update(arguments)
        return [
            {
                "transaction_id": 1,
                "transaction_date": "2026-08-01",
                "transaction_type": "BANK_FEE",
                "description": "Monthly bank fee",
                "amount": -10,
                "category": "Bank Fees",
                "vendor": None,
                "ai_suggested_category": None,
                "ai_confidence": None,
                "reconciliation_status": "UNMATCHED",
                "status": "POSTED",
            }
        ]

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "get_transactions",
        fake_get_transactions,
    )

    response = ask_assistant(
        "Show me posted bank fees."
    )

    assert response.tool_name == "get_transactions"
    assert captured["transaction_type"] == "BANK_FEE"
    assert captured["status"] == "POSTED"

    transactions = response.tool_result[0]["result"]

    assert transactions
    assert all(
        transaction["transaction_type"] == "BANK_FEE"
        for transaction in transactions
    )


def test_demo_assistant_filters_by_reconciliation_status(monkeypatch):
    from ai_assistant import TOOL_REGISTRY, ask_assistant

    captured = {}

    def fake_get_transactions(**arguments):
        captured.update(arguments)
        return [
            {
                "transaction_id": 2,
                "transaction_date": "2026-08-02",
                "transaction_type": "EXPENSE",
                "description": "Microsoft subscription",
                "amount": -50,
                "category": "Software",
                "vendor": "Microsoft",
                "ai_suggested_category": None,
                "ai_confidence": None,
                "reconciliation_status": "UNMATCHED",
                "status": "POSTED",
            }
        ]

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "get_transactions",
        fake_get_transactions,
    )

    response = ask_assistant(
        "Show me unmatched Microsoft expenses."
    )

    assert response.tool_name == "get_transactions"
    assert captured["vendor"] == "Microsoft"
    assert captured["transaction_type"] == "EXPENSE"
    assert captured["reconciliation_status"] == "UNMATCHED"


def test_demo_assistant_filters_by_categorization_state(monkeypatch):
    from ai_assistant import TOOL_REGISTRY, ask_assistant

    captured = {}

    def fake_get_transactions(**arguments):
        captured.update(arguments)
        return [
            {
                "transaction_id": 3,
                "transaction_date": "2026-08-03",
                "transaction_type": "EXPENSE",
                "description": "Microsoft subscription",
                "amount": -50,
                "category": "Software",
                "vendor": "Microsoft",
                "ai_suggested_category": None,
                "ai_confidence": None,
                "reconciliation_status": "MATCHED",
                "status": "POSTED",
            }
        ]

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "get_transactions",
        fake_get_transactions,
    )

    response = ask_assistant(
        "Show me categorized Microsoft expenses."
    )

    assert response.tool_name == "get_transactions"
    assert captured["vendor"] == "Microsoft"
    assert captured["transaction_type"] == "EXPENSE"
    assert captured["categorization_state"] == "CATEGORIZED"


def test_demo_assistant_filters_by_ai_confidence(monkeypatch):
    from ai_assistant import TOOL_REGISTRY, ask_assistant

    captured = {}

    def fake_get_transactions(**arguments):
        captured.update(arguments)
        return [
            {
                "transaction_id": 4,
                "transaction_date": "2026-08-04",
                "transaction_type": "EXPENSE",
                "description": "Microsoft subscription",
                "amount": -50,
                "category": None,
                "vendor": "Microsoft",
                "ai_suggested_category": "Software",
                "ai_confidence": 0.90,
                "reconciliation_status": "UNMATCHED",
                "status": "POSTED",
            }
        ]

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "get_transactions",
        fake_get_transactions,
    )

    response = ask_assistant(
        "Show me high-confidence uncategorized Microsoft expenses."
    )

    assert response.tool_name == "get_transactions"
    assert captured["vendor"] == "Microsoft"
    assert captured["transaction_type"] == "EXPENSE"
    assert captured["categorization_state"] == "UNCATEGORIZED"
    assert captured["min_ai_confidence"] == AI_CONFIDENCE_THRESHOLD
    assert captured["max_ai_confidence"] is None


def test_demo_assistant_filtered_transactions():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Show me Software expenses over €50"
    )

    assert response.tool_name == "get_transactions"
    assert response.tool_result is not None




def test_extract_transaction_filters_with_date_range():
    from ai_assistant import _extract_transaction_filters

    result = _extract_transaction_filters(
        "Show me Software expenses over €50 "
        "between 2026-08-01 and 2026-08-31"
    )

    assert result == {
        "category": "Software",
        "vendor": None,
        "transaction_type": "EXPENSE",
        "reconciliation_status": None,
        "categorization_state": None,
        "min_ai_confidence": None,
        "max_ai_confidence": None,
        "min_amount": 50.0,
        "max_amount": None,
        "status": None,
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
    }

def test_demo_assistant_filtered_transactions_with_dates():
    from ai_assistant import ask_assistant

    response = ask_assistant(
        "Show me Software expenses over €50 "
        "between 2026-08-01 and 2026-08-31"
    )

    assert response.tool_name == "get_transactions"
    assert response.tool_result is not None


def test_extract_amount_filters_supports_roadmap_phrases():
    from ai_assistant import _extract_amount_filters

    examples = {
        "transactions over 50": (50.0, None),
        "transactions above €50": (50.0, None),
        "transactions more than €50": (50.0, None),
        "transactions at least €50": (50.0, None),
        "transactions under €100": (None, 100.0),
        "transactions below 100": (None, 100.0),
        "transactions less than 100 euros": (None, 100.0),
        "transactions at most €100": (None, 100.0),
        "transactions between €50 and €200": (50.0, 200.0),
    }

    for question, expected in examples.items():
        assert _extract_amount_filters(question) == expected


def test_extract_amount_filters_ignores_confidence_and_ambiguous_ranges():
    from ai_assistant import _extract_amount_filters

    assert _extract_amount_filters(
        "Show me AI suggestions below 80% confidence."
    ) == (None, None)
    assert _extract_amount_filters(
        "Show me transactions between a little and a lot."
    ) == (None, None)


def test_extract_relative_date_ranges_and_boundaries():
    from datetime import date

    from ai_assistant import _extract_date_range

    reference_date = date(2026, 3, 15)

    assert _extract_date_range("transactions this month", reference_date) == (
        "2026-03-01",
        "2026-03-15",
    )
    assert _extract_date_range("transactions last month", reference_date) == (
        "2026-02-01",
        "2026-02-28",
    )
    assert _extract_date_range("transactions this year", reference_date) == (
        "2026-01-01",
        "2026-03-15",
    )
    assert _extract_date_range("transactions last 30 days", reference_date) == (
        "2026-02-14",
        "2026-03-15",
    )
    assert _extract_date_range(
        "transactions last month",
        date(2026, 1, 5),
    ) == ("2025-12-01", "2025-12-31")
    assert _extract_date_range(
        "transactions last month",
        date(2024, 3, 1),
    ) == ("2024-02-01", "2024-02-29")


def test_extract_date_range_preserves_explicit_iso_dates():
    from datetime import date

    from ai_assistant import _extract_date_range

    assert _extract_date_range(
        "transactions between 2026-08-01 and 2026-08-31",
        date(2030, 1, 1),
    ) == ("2026-08-01", "2026-08-31")


def test_amount_and_relative_date_queries_route_to_get_transactions():
    from ai_assistant import _select_tools

    assert _select_tools(
        "Show me transactions between €50 and €200."
    ) == ["get_transactions"]
    assert _select_tools(
        "Show me transactions last month."
    ) == ["get_transactions"]


def test_demo_assistant_combines_amount_and_relative_date_filters(monkeypatch):
    from datetime import date

    import ai_assistant

    captured = {}

    def fake_get_transactions(**arguments):
        captured.update(arguments)
        return []

    monkeypatch.setattr(
        ai_assistant,
        "_current_local_date",
        lambda: date(2026, 3, 15),
    )
    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_transactions",
        fake_get_transactions,
    )

    response = ai_assistant.ask_assistant(
        "Show me posted Microsoft Software expenses between €50 and €200 "
        "last month."
    )

    assert response.tool_name == "get_transactions"
    assert captured["category"] == "Software"
    assert captured["vendor"] == "Microsoft"
    assert captured["transaction_type"] == "EXPENSE"
    assert captured["min_amount"] == 50.0
    assert captured["max_amount"] == 200.0
    assert captured["status"] == "POSTED"
    assert captured["start_date"] == "2026-02-01"
    assert captured["end_date"] == "2026-02-28"


def test_extract_transaction_filters_combines_roadmap_target():
    from ai_assistant import _extract_transaction_filters

    result = _extract_transaction_filters(
        "Show me posted Microsoft Software expenses over €50 "
        "between 2026-08-01 and 2026-08-31."
    )

    assert result == {
        "category": "Software",
        "vendor": "Microsoft",
        "transaction_type": "EXPENSE",
        "reconciliation_status": None,
        "categorization_state": None,
        "min_ai_confidence": None,
        "max_ai_confidence": None,
        "min_amount": 50.0,
        "max_amount": None,
        "status": "POSTED",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
    }


def test_roadmap_target_routes_get_transactions_once():
    from ai_assistant import _select_tools

    assert _select_tools(
        "Show me posted Microsoft Software expenses over €50 "
        "between 2026-08-01 and 2026-08-31."
    ) == ["get_transactions"]


def test_demo_assistant_combines_phase_one_filters(monkeypatch):
    from datetime import date

    import ai_assistant

    calls = []

    def fake_get_transactions(**arguments):
        calls.append(arguments)
        return []

    monkeypatch.setattr(
        ai_assistant,
        "_current_local_date",
        lambda: date(2026, 3, 15),
    )
    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_transactions",
        fake_get_transactions,
    )

    response = ai_assistant.ask_assistant(
        "Show me posted unmatched uncategorized Microsoft expenses "
        "between €50 and €200 below 80% confidence last month."
    )

    assert response.tool_name == "get_transactions"
    assert len(calls) == 1
    assert calls[0] == {
        "category": None,
        "vendor": "Microsoft",
        "transaction_type": "EXPENSE",
        "reconciliation_status": "UNMATCHED",
        "categorization_state": "UNCATEGORIZED",
        "min_ai_confidence": None,
        "max_ai_confidence": 0.80,
        "min_amount": 50.0,
        "max_amount": 200.0,
        "status": "POSTED",
        "start_date": "2026-02-01",
        "end_date": "2026-02-28",
    }


def test_spending_by_category_uses_accounting_semantics_and_binds(monkeypatch):
    import re

    import analytics

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, parameters):
            captured["statement"] = statement
            captured["parameters"] = parameters

        def fetchall(self):
            return [
                ("Software", 175.5, 2),
                ("Uncategorized", 25, 1),
            ]

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )

    result = analytics.get_spending_by_category(
        category="Software",
        start_date="2026-08-01",
        end_date="2026-08-31",
    )

    assert result == [
        {
            "category": "Software",
            "total_spending": 175.5,
            "transaction_count": 2,
        },
        {
            "category": "Uncategorized",
            "total_spending": 25,
            "transaction_count": 1,
        },
    ]
    assert "FROM financial_transactions" in captured["statement"]
    assert "FROM orders" not in captured["statement"]
    assert "transaction_type IN ('EXPENSE', 'BANK_FEE')" in captured["statement"]
    assert "status = 'POSTED'" in captured["statement"]
    assert "SUM(ABS(amount))" in captured["statement"]
    assert "NVL(category, 'Uncategorized')" in captured["statement"]
    assert set(re.findall(r":([a-z_]+)", captured["statement"])) == {
        "category",
        "start_date",
        "end_date",
    }
    assert captured["parameters"] == {
        "category": "Software",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
    }
    assert "2026-08-01" not in captured["statement"]
    assert "2026-08-31" not in captured["statement"]
    assert captured["closed"] is True


def test_vendor_totals_uses_accounting_semantics_and_binds(monkeypatch):
    import re

    import analytics

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, parameters):
            captured["statement"] = statement
            captured["parameters"] = parameters

        def fetchall(self):
            return [
                ("Microsoft", 150, 2),
                ("No vendor", 10, 1),
            ]

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )

    result = analytics.get_vendor_totals(
        vendor="micro",
        start_date="2026-08-01",
        end_date="2026-08-31",
        limit=5,
    )

    assert result == [
        {
            "vendor": "Microsoft",
            "total_spending": 150,
            "transaction_count": 2,
        },
        {
            "vendor": "No vendor",
            "total_spending": 10,
            "transaction_count": 1,
        },
    ]
    assert "FROM financial_transactions" in captured["statement"]
    assert "FROM orders" not in captured["statement"]
    assert "transaction_type IN ('EXPENSE', 'BANK_FEE')" in captured["statement"]
    assert "status = 'POSTED'" in captured["statement"]
    assert "SUM(ABS(amount))" in captured["statement"]
    assert "NVL(vendor, 'No vendor')" in captured["statement"]
    assert set(re.findall(r":([a-z_]+)", captured["statement"])) == {
        "vendor",
        "start_date",
        "end_date",
        "limit",
    }
    assert captured["parameters"] == {
        "vendor": "micro",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
        "limit": 5,
    }
    assert "micro" not in captured["statement"]
    assert captured["closed"] is True


def test_phase_two_spending_queries_route_without_raw_transactions():
    from ai_assistant import _select_tools

    examples = {
        "How much did we spend on Software?": "get_spending_by_category",
        "Which expense category costs the most?": "get_spending_by_category",
        "Show spending by category last month.": "get_spending_by_category",
        "Which vendors cost us the most?": "get_vendor_totals",
        "How much did we spend with Microsoft?": "get_vendor_totals",
        "Show top 5 vendor spending this year.": "get_vendor_totals",
    }

    for question, expected_tool in examples.items():
        assert _select_tools(question) == [expected_tool]


def test_spending_formatters_handle_results_and_empty_lists():
    from ai_assistant import (
        _format_spending_by_category,
        _format_vendor_totals,
    )

    category_message = _format_spending_by_category([
        {
            "category": "Software",
            "total_spending": 175.5,
            "transaction_count": 2,
        },
        {
            "category": "Uncategorized",
            "total_spending": 25,
            "transaction_count": 1,
        },
    ])
    vendor_message = _format_vendor_totals([
        {
            "vendor": "Microsoft",
            "total_spending": 150,
            "transaction_count": 2,
        },
        {
            "vendor": "No vendor",
            "total_spending": 10,
            "transaction_count": 1,
        },
    ])

    assert "Software: €175.50 across 2 transaction(s)" in category_message
    assert "Uncategorized: €25.00" in category_message
    assert "Microsoft: €150.00 across 2 transaction(s)" in vendor_message
    assert "No vendor: €10.00" in vendor_message
    assert "No posted expense spending" in _format_spending_by_category([])
    assert "No posted expense spending" in _format_vendor_totals([])


def test_demo_assistant_executes_spending_analytics_generically(monkeypatch):
    from datetime import date

    import ai_assistant

    calls = []

    def fake_category_spending(**arguments):
        calls.append(("get_spending_by_category", arguments))
        return []

    def fake_vendor_totals(**arguments):
        calls.append(("get_vendor_totals", arguments))
        return []

    monkeypatch.setattr(
        ai_assistant,
        "_current_local_date",
        lambda: date(2026, 3, 15),
    )
    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_spending_by_category",
        fake_category_spending,
    )
    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_vendor_totals",
        fake_vendor_totals,
    )

    category_response = ai_assistant.ask_assistant(
        "How much did we spend on Software last month?"
    )
    vendor_response = ai_assistant.ask_assistant(
        "Show top 5 vendor spending between 2026-01-01 and 2026-03-31."
    )

    assert category_response.tool_name == "get_spending_by_category"
    assert vendor_response.tool_name == "get_vendor_totals"
    assert calls == [
        (
            "get_spending_by_category",
            {
                "category": "Software",
                "start_date": "2026-02-01",
                "end_date": "2026-02-28",
            },
        ),
        (
            "get_vendor_totals",
            {
                "vendor": None,
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "limit": 5,
            },
        ),
    ]


def test_phase_one_complex_query_routing_is_preserved():
    from ai_assistant import _select_tools

    assert _select_tools(
        "Show me posted Microsoft Software expenses over €50 "
        "between 2026-08-01 and 2026-08-31."
    ) == ["get_transactions"]


def test_revenue_analysis_uses_accounting_semantics_and_binds(monkeypatch):
    import re

    import analytics

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, parameters):
            captured["statement"] = statement
            captured["parameters"] = parameters

        def fetchall(self):
            return [
                ("2026-07", 100, 1),
                ("2026-08", 250.5, 2),
            ]

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(analytics, "get_connection", lambda: FakeConnection())

    result = analytics.get_revenue_analysis(
        start_date="2026-07-01",
        end_date="2026-08-31",
        period="month",
    )

    assert result == {
        "period": "month",
        "total_revenue": 350.5,
        "transaction_count": 3,
        "periods": [
            {
                "period": "2026-07",
                "total_revenue": 100,
                "transaction_count": 1,
            },
            {
                "period": "2026-08",
                "total_revenue": 250.5,
                "transaction_count": 2,
            },
        ],
    }
    statement = captured["statement"]
    assert "FROM financial_transactions" in statement
    assert "FROM orders" not in statement
    assert "transaction_type = 'SALE'" in statement
    assert "status = 'POSTED'" in statement
    assert "SUM(amount)" in statement
    assert "TRUNC(transaction_date, 'MM')" in statement
    assert set(re.findall(r":([a-z_]+)", statement)) == {
        "start_date",
        "end_date",
    }
    assert captured["parameters"] == {
        "start_date": "2026-07-01",
        "end_date": "2026-08-31",
    }
    assert "2026-07-01" not in statement
    assert "2026-08-31" not in statement
    assert captured["closed"] is True


def test_expense_trends_uses_binds_and_calculates_changes(monkeypatch):
    import re

    import analytics

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, parameters):
            captured["statement"] = statement
            captured["parameters"] = parameters

        def fetchall(self):
            return [
                ("2026-01", 100, 2),
                ("2026-02", 125, 3),
                ("2026-04", 50, 1),
            ]

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(analytics, "get_connection", lambda: FakeConnection())

    result = analytics.get_expense_trends(
        category="Software",
        vendor="micro",
        start_date="2026-01-01",
        end_date="2026-04-30",
        period="month",
    )

    assert result["total_expenses"] == 275
    assert result["transaction_count"] == 6
    assert result["periods"][0]["change_amount"] is None
    assert result["periods"][0]["change_percentage"] is None
    assert result["periods"][1]["change_amount"] == 25
    assert result["periods"][1]["change_percentage"] == 25
    assert result["periods"][2]["period"] == "2026-03"
    assert result["periods"][2]["total_expenses"] == 0
    assert result["periods"][2]["transaction_count"] == 0
    assert result["periods"][2]["change_percentage"] == -100
    assert result["periods"][3]["change_amount"] == 50
    assert result["periods"][3]["change_percentage"] is None
    statement = captured["statement"]
    assert "FROM financial_transactions" in statement
    assert "FROM orders" not in statement
    assert "transaction_type IN ('EXPENSE', 'BANK_FEE')" in statement
    assert "status = 'POSTED'" in statement
    assert "SUM(ABS(amount))" in statement
    assert set(re.findall(r":([a-z_]+)", statement)) == {
        "category",
        "vendor",
        "start_date",
        "end_date",
    }
    assert captured["parameters"] == {
        "category": "Software",
        "vendor": "micro",
        "start_date": "2026-01-01",
        "end_date": "2026-04-30",
    }
    assert "micro" not in statement
    assert captured["closed"] is True


def test_financial_analytics_handle_empty_periods_and_invalid_grouping(monkeypatch):
    import analytics
    import pytest

    closed = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, statement, parameters):
            pass

        def fetchall(self):
            return []

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            closed.append(True)

    monkeypatch.setattr(analytics, "get_connection", lambda: FakeConnection())

    assert analytics.get_revenue_analysis(period="year") == {
        "period": "year",
        "total_revenue": 0,
        "transaction_count": 0,
        "periods": [],
    }
    assert analytics.get_expense_trends(period="month") == {
        "period": "month",
        "category": None,
        "vendor": None,
        "total_expenses": 0,
        "transaction_count": 0,
        "periods": [],
    }
    assert len(closed) == 2

    with pytest.raises(ValueError, match="period must be"):
        analytics.get_revenue_analysis(period="quarter")


def test_named_month_date_ranges_are_deterministic_at_boundaries():
    from datetime import date

    from ai_assistant import _extract_date_range

    assert _extract_date_range(
        "How much revenue did we make in August?",
        date(2026, 9, 3),
    ) == ("2026-08-01", "2026-08-31")
    assert _extract_date_range(
        "Show revenue in December.",
        date(2026, 9, 3),
    ) == ("2025-12-01", "2025-12-31")
    assert _extract_date_range(
        "Show expenses in February 2024.",
        date(2026, 9, 3),
    ) == ("2024-02-01", "2024-02-29")


def test_revenue_and_expense_trend_queries_route_without_raw_transactions():
    from ai_assistant import _select_tools

    examples = {
        "How much revenue did we make in August?": "get_revenue_analysis",
        "Show monthly revenue.": "get_revenue_analysis",
        "Show annual revenue this year.": "get_revenue_analysis",
        "Show monthly expenses.": "get_expense_trends",
        "Show month-over-month Software expense trends.": "get_expense_trends",
        "Show yearly Microsoft spending trends.": "get_expense_trends",
    }

    for question, expected_tool in examples.items():
        assert _select_tools(question) == [expected_tool]


def test_financial_analysis_formatters_handle_results_and_empty_periods():
    from ai_assistant import (
        _format_expense_trends,
        _format_revenue_analysis,
    )

    revenue_message = _format_revenue_analysis({
        "period": "month",
        "total_revenue": 350.5,
        "transaction_count": 3,
        "periods": [
            {
                "period": "2026-08",
                "total_revenue": 350.5,
                "transaction_count": 3,
            },
        ],
    })
    expense_message = _format_expense_trends({
        "period": "month",
        "total_expenses": 225,
        "transaction_count": 5,
        "periods": [
            {
                "period": "2026-01",
                "total_expenses": 100,
                "transaction_count": 2,
                "change_amount": None,
                "change_percentage": None,
            },
            {
                "period": "2026-02",
                "total_expenses": 125,
                "transaction_count": 3,
                "change_amount": 25,
                "change_percentage": 25,
            },
        ],
    })

    assert "Posted sale revenue: €350.50" in revenue_message
    assert "2026-08: €350.50" in revenue_message
    assert "Posted expense trend: €225.00" in expense_message
    assert "+25.00% month over month" in expense_message
    assert "No posted sale revenue" in _format_revenue_analysis({"periods": []})
    assert "No posted expense spending" in _format_expense_trends({"periods": []})


def test_demo_assistant_executes_financial_analysis_generically(monkeypatch):
    from datetime import date

    import ai_assistant

    calls = []

    def fake_revenue(**arguments):
        calls.append(("get_revenue_analysis", arguments))
        return {"periods": []}

    def fake_expenses(**arguments):
        calls.append(("get_expense_trends", arguments))
        return {"periods": []}

    monkeypatch.setattr(
        ai_assistant,
        "_current_local_date",
        lambda: date(2026, 9, 3),
    )
    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_revenue_analysis",
        fake_revenue,
    )
    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_expense_trends",
        fake_expenses,
    )

    revenue_response = ai_assistant.ask_assistant(
        "How much revenue did we make in August?"
    )
    expense_response = ai_assistant.ask_assistant(
        "Show yearly Microsoft expense trends this year."
    )

    assert revenue_response.tool_name == "get_revenue_analysis"
    assert expense_response.tool_name == "get_expense_trends"
    assert calls == [
        (
            "get_revenue_analysis",
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-31",
                "period": "month",
            },
        ),
        (
            "get_expense_trends",
            {
                "category": None,
                "vendor": "Microsoft",
                "start_date": "2026-01-01",
                "end_date": "2026-09-03",
                "period": "year",
            },
        ),
    ]


def test_phase_one_and_existing_spending_routing_remain_preserved():
    from ai_assistant import _select_tools

    assert _select_tools(
        "Show me posted Microsoft Software expenses over €50 "
        "between 2026-08-01 and 2026-08-31."
    ) == ["get_transactions"]
    assert _select_tools(
        "How much did we spend on Software last month?"
    ) == ["get_spending_by_category"]
    assert _select_tools(
        "Show top 5 vendor spending this year."
    ) == ["get_vendor_totals"]


def test_financial_statistics_sql_contract(monkeypatch):
    import analytics

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            captured["sql"] = sql
            captured["binds"] = binds

        def fetchone(self):
            return (
                8,
                76.17,
                129.00,
                5,
                3,
                6,
                2,
            )

    class FakeConnection:
        def __init__(self):
            self.closed = False

        def cursor(self):
            return FakeCursor()

        def close(self):
            self.closed = True

    connection = FakeConnection()

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: connection,
    )

    result = analytics.get_financial_statistics(
        start_date="2026-08-01",
        end_date="2026-08-31",
    )

    sql = " ".join(captured["sql"].split())

    assert "FROM financial_transactions" in sql
    assert "COUNT(*) AS transaction_count" in sql
    assert "AVG(" in sql
    assert "MAX(" in sql
    assert "ABS(amount)" in sql
    assert "transaction_type IN ('EXPENSE', 'BANK_FEE')" in sql
    assert "status = 'POSTED'" in sql
    assert ":start_date" in sql
    assert ":end_date" in sql

    assert captured["binds"] == {
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
    }

    assert result == {
        "transaction_count": 8,
        "average_expense": 76.17,
        "largest_expense": 129.00,
        "posted_count": 5,
        "pending_count": 3,
        "categorized_count": 6,
        "uncategorized_count": 2,
    }

    assert connection.closed is True


def test_financial_statistics_empty_expense_subset(monkeypatch):
    import analytics

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            pass

        def fetchone(self):
            return (
                0,
                None,
                None,
                0,
                0,
                0,
                0,
            )

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )

    assert analytics.get_financial_statistics() == {
        "transaction_count": 0,
        "average_expense": None,
        "largest_expense": None,
        "posted_count": 0,
        "pending_count": 0,
        "categorized_count": 0,
        "uncategorized_count": 0,
    }


def test_financial_statistics_tool_schema():
    from ai_tools import TOOL_DEFINITIONS, TOOL_REGISTRY

    assert "get_financial_statistics" in TOOL_REGISTRY

    tool = next(
        item
        for item in TOOL_DEFINITIONS
        if item["name"] == "get_financial_statistics"
    )

    assert tool["type"] == "function"
    assert set(tool["parameters"]["properties"]) == {
        "start_date",
        "end_date",
    }
    assert tool["parameters"]["required"] == [
        "start_date",
        "end_date",
    ]
    assert tool["parameters"]["additionalProperties"] is False


def test_financial_statistics_queries_route_without_raw_transactions():
    from ai_assistant import _select_tools

    examples = [
        "Show financial statistics.",
        "What is our average expense?",
        "What is our largest expense?",
        "How many transactions are posted versus pending?",
        "How many transactions are categorized versus uncategorized?",
    ]

    for question in examples:
        assert _select_tools(question) == [
            "get_financial_statistics"
        ]


def test_financial_statistics_formatter():
    from ai_assistant import _format_financial_statistics

    message = _format_financial_statistics({
        "transaction_count": 8,
        "average_expense": 76.17,
        "largest_expense": 129,
        "posted_count": 5,
        "pending_count": 3,
        "categorized_count": 6,
        "uncategorized_count": 2,
    })

    assert "8 transaction(s)" in message
    assert "Average posted expense: €76.17" in message
    assert "Largest posted expense: €129.00" in message
    assert "5 posted, 3 pending" in message
    assert "6 categorized, 2 uncategorized" in message

    empty_expense_message = _format_financial_statistics({
        "transaction_count": 0,
        "average_expense": None,
        "largest_expense": None,
        "posted_count": 0,
        "pending_count": 0,
        "categorized_count": 0,
        "uncategorized_count": 0,
    })

    assert "Average posted expense: N/A" in empty_expense_message
    assert "Largest posted expense: N/A" in empty_expense_message


def test_demo_assistant_executes_financial_statistics_generically(
    monkeypatch,
):
    from datetime import date

    import ai_assistant

    calls = []

    def fake_financial_statistics(**arguments):
        calls.append(arguments)

        return {
            "transaction_count": 4,
            "average_expense": 75,
            "largest_expense": 100,
            "posted_count": 3,
            "pending_count": 1,
            "categorized_count": 3,
            "uncategorized_count": 1,
        }

    monkeypatch.setattr(
        ai_assistant,
        "_current_local_date",
        lambda: date(2026, 9, 3),
    )

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_financial_statistics",
        fake_financial_statistics,
    )

    response = ai_assistant.ask_assistant(
        "What is our average expense this month?"
    )

    assert response.tool_name == "get_financial_statistics"
    assert len(calls) == 1
    assert calls[0] == {
        "start_date": "2026-09-01",
        "end_date": "2026-09-03",
    }
    assert "Average posted expense: €75.00" in response.message


def test_uncategorized_investigation_read_only_contract(monkeypatch):
    import accounting_rag
    import analytics
    import llm_categorizer

    from accounting_rag import AccountingContext
    from llm_categorizer import CategorySuggestion

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            captured["sql"] = sql
            captured["binds"] = binds

        def fetchone(self):
            return (
                7,
                "2026-09-01",
                "EXPENSE",
                "Microsoft 365 subscription",
                -120.0,
                None,
                "Microsoft",
                "Software",
                0.70,
                "UNMATCHED",
                "POSTED",
            )

    class FakeConnection:
        def __init__(self):
            self.closed = False
            self.commit_called = False

        def cursor(self):
            return FakeCursor()

        def commit(self):
            self.commit_called = True
            raise AssertionError(
                "Read-only investigation must not commit"
            )

        def close(self):
            self.closed = True

    connection = FakeConnection()

    context = AccountingContext(
        categories=[
            {
                "category_id": 3,
                "account_code": "6100",
                "account_name": "Software",
                "account_type": "EXPENSE",
            },
            {
                "category_id": 4,
                "account_code": "6200",
                "account_name": "Office Supplies",
                "account_type": "EXPENSE",
            },
        ],
        examples=[
            {
                "transaction_id": 2,
                "description": "Microsoft subscription",
                "vendor": "Microsoft",
                "category": "Software",
            },
        ],
    )

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: connection,
    )
    monkeypatch.setattr(
        accounting_rag,
        "get_accounting_context",
        lambda description, vendor: context,
    )
    monkeypatch.setattr(
        llm_categorizer,
        "suggest_transaction_category",
        lambda **kwargs: CategorySuggestion(
            category="Software",
            confidence=0.95,
        ),
    )

    result = analytics.investigate_uncategorized_transaction(
        transaction_id=7,
    )

    normalized_sql = " ".join(captured["sql"].split()).upper()

    assert "FROM FINANCIAL_TRANSACTIONS" in normalized_sql
    assert "WHERE TRANSACTION_ID = :TRANSACTION_ID" in normalized_sql
    assert "UPDATE " not in normalized_sql
    assert "INSERT " not in normalized_sql
    assert "DELETE " not in normalized_sql

    assert captured["binds"] == {
        "transaction_id": 7,
    }

    assert result["transaction"]["transaction_id"] == 7
    assert result["transaction"]["category"] is None
    assert result["investigation_status"] == "RECOMMENDATION_READY"

    assert result["current_ai_suggestion"] == {
        "category": "Software",
        "confidence": 0.70,
    }

    assert result["recommendation"]["category"] == "Software"
    assert result["recommendation"]["confidence"] == 0.95
    assert result["recommendation"]["high_confidence"] is True
    assert result["requires_human_review"] is True

    assert result["evidence"]["supporting_example_count"] == 1
    assert result["evidence"]["historical_examples"][0][
        "transaction_id"
    ] == 2
    assert (
        result["evidence"]["historical_examples"][0][
            "retrieval_score"
        ]
        > 0
    )
    assert "EXACT_VENDOR" in (
        result["evidence"]["historical_examples"][0][
            "match_reasons"
        ]
    )
    assert result["evidence"]["retrieved_categories"] == [
        "Software"
    ]
    assert (
        result["evidence"]["retrieved_category_conflict"]
        is False
    )

    assert connection.commit_called is False
    assert connection.closed is True


def test_uncategorized_investigation_rejects_invalid_demo_category(
    monkeypatch,
):
    import accounting_rag
    import analytics
    import llm_categorizer
    import pytest

    from accounting_rag import AccountingContext
    from llm_categorizer import CategorySuggestion

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            pass

        def fetchone(self):
            return (
                7,
                "2026-09-01",
                "EXPENSE",
                "Unknown expense",
                -50.0,
                None,
                "Unknown Vendor",
                None,
                None,
                "UNMATCHED",
                "POSTED",
            )

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    context = AccountingContext(
        categories=[
            {
                "category_id": 3,
                "account_code": "6100",
                "account_name": "Software",
                "account_type": "EXPENSE",
            },
        ],
        examples=[],
    )

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )
    monkeypatch.setattr(
        accounting_rag,
        "get_accounting_context",
        lambda description, vendor: context,
    )
    monkeypatch.setattr(
        llm_categorizer,
        "suggest_transaction_category",
        lambda **kwargs: CategorySuggestion(
            category="Office Supplies",
            confidence=0.10,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Invalid accounting category returned by AI",
    ):
        analytics.investigate_uncategorized_transaction(
            transaction_id=7,
        )


def test_uncategorized_investigation_handles_categorized_transaction(
    monkeypatch,
):
    import analytics

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            pass

        def fetchone(self):
            return (
                8,
                "2026-09-01",
                "EXPENSE",
                "Microsoft 365",
                -120.0,
                "Software",
                "Microsoft",
                "Software",
                0.95,
                "MATCHED",
                "POSTED",
            )

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )

    result = analytics.investigate_uncategorized_transaction(
        transaction_id=8,
    )

    assert result["investigation_status"] == "ALREADY_CATEGORIZED"
    assert result["transaction"]["category"] == "Software"
    assert result["recommendation"] is None
    assert result["requires_human_review"] is False


def test_uncategorized_investigation_handles_missing_transaction(
    monkeypatch,
):
    import analytics

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            pass

        def fetchone(self):
            return None

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )

    assert (
        analytics.investigate_uncategorized_transaction(
            transaction_id=999999,
        )
        is None
    )


def test_uncategorized_investigation_tool_schema():
    from ai_tools import TOOL_DEFINITIONS, TOOL_REGISTRY

    assert "investigate_uncategorized_transaction" in TOOL_REGISTRY

    tool = next(
        item
        for item in TOOL_DEFINITIONS
        if item["name"] == "investigate_uncategorized_transaction"
    )

    assert tool["type"] == "function"
    assert set(tool["parameters"]["properties"]) == {
        "transaction_id",
    }
    assert tool["parameters"]["required"] == ["transaction_id"]
    assert tool["parameters"]["properties"]["transaction_id"][
        "minimum"
    ] == 1
    assert tool["parameters"]["additionalProperties"] is False


def test_uncategorized_investigation_demo_routing():
    from ai_assistant import _select_tools

    questions = [
        "Why is transaction 7 uncategorized?",
        "What category would you recommend for transaction 7 and why?",
        (
            "What evidence supports the recommendation "
            "for transaction 7?"
        ),
    ]

    for question in questions:
        assert _select_tools(question) == [
            "investigate_uncategorized_transaction"
        ]


def test_uncategorized_investigation_formatter():
    from ai_assistant import _format_uncategorized_investigation

    result = {
        "transaction": {
            "transaction_id": 7,
            "transaction_date": "2026-09-01",
            "transaction_type": "EXPENSE",
            "description": "Microsoft 365 subscription",
            "amount": -120,
            "category": None,
            "vendor": "Microsoft",
            "reconciliation_status": "UNMATCHED",
            "status": "POSTED",
        },
        "investigation_status": "RECOMMENDATION_READY",
        "current_ai_suggestion": {
            "category": "Software",
            "confidence": 0.70,
        },
        "evidence": {
            "available_categories": [
                "Software",
                "Office Supplies",
            ],
            "historical_examples": [],
            "supporting_example_count": 1,
        },
        "recommendation": {
            "category": "Software",
            "confidence": 0.95,
            "high_confidence": True,
            "rationale": (
                "1 confirmed historical example supports Software."
            ),
        },
        "requires_human_review": True,
    }

    message = _format_uncategorized_investigation(result)

    assert "Transaction 7 remains uncategorized" in message
    assert "€120.00" in message
    assert "Stored AI suggestion: Software at 70%" in message
    assert "not approved accounting truth" in message
    assert "Read-only recommendation: Software at 95%" in message
    assert "Supporting confirmed examples: 1" in message
    assert "requires human review and approval" in message


def test_demo_assistant_executes_uncategorized_investigation_generically(
    monkeypatch,
):
    import ai_assistant

    calls = []

    def fake_investigation(**arguments):
        calls.append(arguments)

        return {
            "transaction": {
                "transaction_id": 7,
                "description": "Microsoft 365",
                "vendor": "Microsoft",
                "amount": -120,
                "category": None,
            },
            "investigation_status": "RECOMMENDATION_READY",
            "current_ai_suggestion": None,
            "evidence": {
                "available_categories": ["Software"],
                "historical_examples": [],
                "supporting_example_count": 0,
            },
            "recommendation": {
                "category": "Software",
                "confidence": 0.95,
                "high_confidence": True,
                "rationale": "Vendor and description evidence.",
            },
            "requires_human_review": True,
        }

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "investigate_uncategorized_transaction",
        fake_investigation,
    )

    response = ai_assistant.ask_assistant(
        "Why is transaction 7 uncategorized?"
    )

    assert response.tool_name == (
        "investigate_uncategorized_transaction"
    )
    assert calls == [
        {
            "transaction_id": 7,
        }
    ]
    assert "Read-only recommendation: Software" in response.message


def test_reconciliation_investigation_read_only_contract(monkeypatch):
    from datetime import datetime

    import analytics

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            captured["sql"] = sql
            captured["binds"] = binds

        def fetchone(self):
            return (
                10,
                datetime(2026, 8, 15),
                "AWS payment",
                -129.0,
                "UNMATCHED",
                1,
                "POSSIBLE_MATCH",
                0.84,
                None,
                datetime(2026, 8, 13),
                "AWS monthly payment",
                -129.0,
                "Amazon Web Services",
                "Software",
                "EXPENSE",
                "POSTED",
                "UNMATCHED",
            )

    class FakeConnection:
        def __init__(self):
            self.closed = False
            self.commit_called = False

        def cursor(self):
            return FakeCursor()

        def commit(self):
            self.commit_called = True
            raise AssertionError(
                "Read-only investigation must not commit"
            )

        def close(self):
            self.closed = True

    connection = FakeConnection()

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: connection,
    )

    result = analytics.investigate_reconciliation_issue(
        bank_transaction_id=10,
    )

    sql = " ".join(captured["sql"].split()).upper()

    assert "FROM BANK_TRANSACTIONS BT" in sql
    assert "LEFT JOIN FINANCIAL_TRANSACTIONS FT" in sql
    assert (
        "WHERE BT.BANK_TRANSACTION_ID = :BANK_TRANSACTION_ID"
        in sql
    )
    assert "UPDATE " not in sql
    assert "INSERT " not in sql
    assert "DELETE " not in sql

    assert captured["binds"] == {
        "bank_transaction_id": 10,
    }

    assert result["bank_transaction"][
        "bank_transaction_id"
    ] == 10
    assert result["candidate_match"]["transaction_id"] == 1
    assert result["match"]["match_type"] == "POSSIBLE_MATCH"
    assert result["match"]["match_confidence"] == 0.84

    assert result["evidence"]["amount_difference"] == 0.0
    assert result["evidence"]["amount_matches"] is True
    assert result["evidence"]["date_difference_days"] == 2
    assert result["evidence"][
        "description_token_overlap"
    ] == 1.0

    assert result["assessment"]["code"] == (
        "POSSIBLE_MATCH_REVIEW"
    )
    assert result["requires_human_review"] is True
    assert connection.commit_called is False
    assert connection.closed is True


def test_reconciliation_investigation_handles_no_match(
    monkeypatch,
):
    from datetime import datetime

    import analytics

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            pass

        def fetchone(self):
            return (
                3,
                datetime(2026, 8, 20),
                "Unknown withdrawal",
                -75.0,
                "UNMATCHED",
                None,
                "NO_MATCH",
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )

    result = analytics.investigate_reconciliation_issue(
        bank_transaction_id=3,
    )

    assert result["candidate_match"] is None
    assert result["assessment"]["code"] == "NO_MATCH_FOUND"
    assert result["requires_human_review"] is True
    assert "no linked financial transaction" in (
        result["assessment"]["explanation"].lower()
    )


def test_reconciliation_investigation_handles_matched_item(
    monkeypatch,
):
    from datetime import datetime

    import analytics

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            pass

        def fetchone(self):
            return (
                4,
                datetime(2026, 8, 20),
                "Supplier payment",
                -200.0,
                "MATCHED",
                5,
                "POSSIBLE_MATCH",
                0.90,
                None,
                datetime(2026, 8, 20),
                "Supplier payment",
                -200.0,
                "Supplier",
                "Office Supplies",
                "EXPENSE",
                "POSTED",
                "MATCHED",
            )

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )

    result = analytics.investigate_reconciliation_issue(
        bank_transaction_id=4,
    )

    assert result["assessment"]["code"] == "ALREADY_MATCHED"
    assert result["requires_human_review"] is False


def test_reconciliation_investigation_handles_missing_item(
    monkeypatch,
):
    import analytics

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, binds):
            pass

        def fetchone(self):
            return None

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        analytics,
        "get_connection",
        lambda: FakeConnection(),
    )

    assert (
        analytics.investigate_reconciliation_issue(
            bank_transaction_id=999999,
        )
        is None
    )


def test_reconciliation_investigation_tool_schema():
    from ai_tools import TOOL_DEFINITIONS, TOOL_REGISTRY

    assert "investigate_reconciliation_issue" in TOOL_REGISTRY

    tool = next(
        item
        for item in TOOL_DEFINITIONS
        if item["name"] == "investigate_reconciliation_issue"
    )

    assert tool["type"] == "function"
    assert set(tool["parameters"]["properties"]) == {
        "bank_transaction_id",
    }
    assert tool["parameters"]["required"] == [
        "bank_transaction_id",
    ]
    assert tool["parameters"]["properties"][
        "bank_transaction_id"
    ]["minimum"] == 1
    assert tool["parameters"]["additionalProperties"] is False


def test_reconciliation_investigation_demo_routing():
    from ai_assistant import _select_tools

    assert _select_tools(
        "Why is bank transaction 10 unmatched?"
    ) == [
        "investigate_reconciliation_issue"
    ]

    assert _select_tools(
        "What evidence supports the possible match "
        "for bank transaction 10?"
    ) == [
        "investigate_reconciliation_issue"
    ]

    assert _select_tools(
        "Investigate bank transaction 10."
    ) == [
        "investigate_reconciliation_issue"
    ]

    # Bulk review remains on the existing queue tool.
    assert _select_tools(
        "Which reconciliation issues need attention?"
    ) == [
        "get_reconciliation_review"
    ]


def test_reconciliation_investigation_formatter():
    from ai_assistant import _format_reconciliation_investigation

    result = {
        "bank_transaction": {
            "bank_transaction_id": 10,
            "transaction_date": "2026-08-15",
            "description": "AWS payment",
            "amount": -129,
            "status": "UNMATCHED",
            "stored_investigation_status": None,
        },
        "candidate_match": {
            "transaction_id": 1,
            "transaction_date": "2026-08-13",
            "description": "AWS monthly payment",
            "amount": -129,
            "vendor": "Amazon Web Services",
            "category": "Software",
            "transaction_type": "EXPENSE",
            "status": "POSTED",
            "reconciliation_status": "UNMATCHED",
        },
        "match": {
            "match_type": "POSSIBLE_MATCH",
            "match_confidence": 0.84,
        },
        "evidence": {
            "amount_difference": 0.0,
            "amount_matches": True,
            "date_difference_days": 2,
            "description_token_overlap": 0.5,
        },
        "assessment": {
            "code": "POSSIBLE_MATCH_REVIEW",
            "explanation": (
                "The evidence supports a possible match, "
                "but it is not finalized."
            ),
        },
        "requires_human_review": True,
    }

    message = _format_reconciliation_investigation(result)

    assert "bank transaction 10" in message
    assert "€-129.00" in message
    assert "POSSIBLE_MATCH" in message
    assert "84%" in message
    assert "candidate transaction 1" in message
    assert "amount difference €0.00" in message
    assert "date difference 2 day(s)" in message
    assert "description token overlap 50%" in message
    assert "No reconciliation state was changed" in message
    assert "Human review is required" in message


def test_demo_assistant_executes_reconciliation_investigation_generically(
    monkeypatch,
):
    import ai_assistant

    calls = []

    def fake_investigation(**arguments):
        calls.append(arguments)

        return {
            "bank_transaction": {
                "bank_transaction_id": 10,
                "description": "AWS payment",
                "amount": -129,
                "status": "UNMATCHED",
                "stored_investigation_status": None,
            },
            "candidate_match": None,
            "match": {
                "match_type": "NO_MATCH",
                "match_confidence": 0,
            },
            "evidence": {
                "amount_difference": None,
                "amount_matches": None,
                "date_difference_days": None,
                "description_token_overlap": None,
            },
            "assessment": {
                "code": "NO_MATCH_FOUND",
                "explanation": (
                    "No linked financial transaction candidate exists."
                ),
            },
            "requires_human_review": True,
        }

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "investigate_reconciliation_issue",
        fake_investigation,
    )

    response = ai_assistant.ask_assistant(
        "Why is bank transaction 10 unmatched?"
    )

    assert response.tool_name == (
        "investigate_reconciliation_issue"
    )
    assert calls == [
        {
            "bank_transaction_id": 10,
        }
    ]
    assert "No reconciliation state was changed" in (
        response.message
    )


def test_financial_anomalies_read_only_contract(monkeypatch):
    from datetime import datetime
    import analytics

    captured = {}
    rows = [
        (1, datetime(2026, 8, 1), "EXPENSE", "Annual software license", -300.0, "Software", "Microsoft", "MATCHED", "POSTED"),
        (2, datetime(2026, 8, 2), "EXPENSE", "Printer paper", -50.0, "Office Supplies", "Office Depot", "MATCHED", "POSTED"),
        (3, datetime(2026, 8, 2), "EXPENSE", "Printer paper", -50.0, "Office Supplies", "Office Depot", "MATCHED", "POSTED"),
        (4, datetime(2026, 8, 4), "BANK_FEE", "Monthly bank fee", -10.0, "Bank Fees", None, "MATCHED", "POSTED"),
        (5, datetime(2026, 9, 4), "BANK_FEE", "Monthly bank fee", -10.0, "Bank Fees", None, "MATCHED", "POSTED"),
    ]

    class FakeCursor:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            return False
        def execute(self, sql, binds):
            captured["sql"] = sql
            captured["binds"] = binds
        def fetchall(self):
            return rows

    class FakeConnection:
        def __init__(self):
            self.commit_called = False
            self.closed = False
        def cursor(self):
            return FakeCursor()
        def commit(self):
            self.commit_called = True
            raise AssertionError("Anomaly detection must not commit")
        def close(self):
            self.closed = True

    connection = FakeConnection()
    monkeypatch.setattr(analytics, "get_connection", lambda: connection)

    result = analytics.get_financial_anomalies(
        start_date="2026-08-01",
        end_date="2026-09-30",
    )

    sql = " ".join(captured["sql"].split()).upper()
    assert "FROM FINANCIAL_TRANSACTIONS" in sql
    assert "TRANSACTION_TYPE IN ('EXPENSE', 'BANK_FEE')" in sql
    assert "STATUS = 'POSTED'" in sql
    assert "UPDATE " not in sql
    assert "INSERT " not in sql
    assert "DELETE " not in sql
    assert captured["binds"] == {
        "start_date": "2026-08-01",
        "end_date": "2026-09-30",
    }

    assert result["baseline"]["posted_expense_count"] == 5
    assert result["baseline"]["average_expense"] == 84.0
    assert result["baseline"]["large_expense_threshold"] == 126.0
    assert result["anomaly_count"] == 3

    by_type = {item["anomaly_type"]: item for item in result["anomalies"]}
    assert set(by_type) == {
        "LARGE_EXPENSE",
        "DUPLICATE_TRANSACTION",
        "REPEATED_BANK_FEE",
    }
    assert by_type["LARGE_EXPENSE"]["transaction_ids"] == [1]
    assert by_type["DUPLICATE_TRANSACTION"]["transaction_ids"] == [2, 3]
    assert by_type["REPEATED_BANK_FEE"]["transaction_ids"] == [4, 5]
    assert all(item["requires_human_review"] is True for item in result["anomalies"])
    assert connection.commit_called is False
    assert connection.closed is True


def test_financial_anomalies_can_return_no_signals(monkeypatch):
    from datetime import datetime
    import analytics

    class FakeCursor:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            return False
        def execute(self, sql, binds):
            pass
        def fetchall(self):
            return [
                (1, datetime(2026, 8, 1), "EXPENSE", "Software subscription", -50.0, "Software", "Microsoft", "MATCHED", "POSTED"),
                (2, datetime(2026, 8, 2), "EXPENSE", "Office supplies", -75.0, "Office Supplies", "Office Depot", "MATCHED", "POSTED"),
            ]

    class FakeConnection:
        def cursor(self):
            return FakeCursor()
        def close(self):
            pass

    monkeypatch.setattr(analytics, "get_connection", lambda: FakeConnection())
    result = analytics.get_financial_anomalies()
    assert result["anomaly_count"] == 0
    assert result["anomalies"] == []
    assert result["baseline"]["posted_expense_count"] == 2


def test_financial_anomalies_need_baseline_for_large_expense(monkeypatch):
    from datetime import datetime
    import analytics

    class FakeCursor:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            return False
        def execute(self, sql, binds):
            pass
        def fetchall(self):
            return [
                (1, datetime(2026, 8, 1), "EXPENSE", "One-time purchase", -1000.0, "Office Supplies", "Vendor", "MATCHED", "POSTED"),
            ]

    class FakeConnection:
        def cursor(self):
            return FakeCursor()
        def close(self):
            pass

    monkeypatch.setattr(analytics, "get_connection", lambda: FakeConnection())
    result = analytics.get_financial_anomalies()
    large_expenses = [
        item for item in result["anomalies"]
        if item["anomaly_type"] == "LARGE_EXPENSE"
    ]
    assert large_expenses == []
    assert result["rules"]["large_expense"]["minimum_baseline_count"] == 3


def test_financial_anomalies_tool_schema():
    from ai_tools import TOOL_DEFINITIONS, TOOL_REGISTRY

    assert "get_financial_anomalies" in TOOL_REGISTRY
    tool = next(
        item for item in TOOL_DEFINITIONS
        if item["name"] == "get_financial_anomalies"
    )
    assert tool["type"] == "function"
    assert set(tool["parameters"]["properties"]) == {"start_date", "end_date"}
    assert tool["parameters"]["required"] == ["start_date", "end_date"]
    assert tool["parameters"]["additionalProperties"] is False


def test_financial_anomalies_demo_routing():
    from ai_assistant import _select_tools

    examples = [
        "Which transactions look unusual?",
        "Which accounting anomalies need attention?",
        "Are there any unusually large expenses?",
        "Do any transactions look like duplicates?",
        "Show me repeated bank fees that look suspicious.",
    ]
    for question in examples:
        assert _select_tools(question) == ["get_financial_anomalies"]

    assert _select_tools("What is our largest expense?") == [
        "get_financial_statistics"
    ]


def test_financial_anomalies_formatter():
    from ai_assistant import _format_financial_anomalies

    result = {
        "baseline": {
            "posted_expense_count": 5,
            "average_expense": 84.0,
            "large_expense_threshold": 126.0,
        },
        "anomaly_count": 2,
        "anomalies": [
            {
                "anomaly_type": "LARGE_EXPENSE",
                "severity": "HIGH",
                "transaction_ids": [1],
                "reason": "Posted expense exceeds the threshold.",
                "requires_human_review": True,
            },
            {
                "anomaly_type": "DUPLICATE_TRANSACTION",
                "severity": "MEDIUM",
                "transaction_ids": [2, 3],
                "reason": "Two exact duplicate-looking rows.",
                "requires_human_review": True,
            },
        ],
    }
    message = _format_financial_anomalies(result)
    assert "2 anomaly signal(s)" in message
    assert "average €84.00" in message
    assert "threshold €126.00" in message
    assert "[HIGH] LARGE_EXPENSE" in message
    assert "transaction(s) 1" in message
    assert "[MEDIUM] DUPLICATE_TRANSACTION" in message
    assert "transaction(s) 2, 3" in message
    assert "not confirmed accounting errors" in message
    assert "No accounting state was changed" in message


def test_demo_assistant_executes_financial_anomalies_generically(monkeypatch):
    import ai_assistant

    calls = []

    def fake_anomalies(**arguments):
        calls.append(arguments)
        return {
            "baseline": {
                "posted_expense_count": 3,
                "average_expense": 100.0,
                "large_expense_threshold": 150.0,
            },
            "anomaly_count": 1,
            "anomalies": [
                {
                    "anomaly_type": "LARGE_EXPENSE",
                    "severity": "MEDIUM",
                    "transaction_ids": [7],
                    "reason": "Expense exceeds threshold.",
                    "requires_human_review": True,
                }
            ],
        }

    monkeypatch.setitem(
        ai_assistant.TOOL_REGISTRY,
        "get_financial_anomalies",
        fake_anomalies,
    )
    response = ai_assistant.ask_assistant(
        "Which transactions look unusual?"
    )
    assert response.tool_name == "get_financial_anomalies"
    assert calls == [{"start_date": None, "end_date": None}]
    assert "LARGE_EXPENSE" in response.message
    assert "No accounting state was changed" in response.message
def test_rag_ranking_prioritizes_exact_vendor():
    from accounting_rag import (
        rank_accounting_examples,
    )

    candidates = [
        {
            "transaction_id": 1,
            "description": "Cloud software subscription",
            "vendor": "Other Vendor",
            "category": "Software",
        },
        {
            "transaction_id": 2,
            "description": "General subscription",
            "vendor": "Microsoft",
            "category": "Software",
        },
    ]

    ranked = rank_accounting_examples(
        description="Cloud software subscription",
        vendor="Microsoft",
        candidates=candidates,
    )

    assert [
        item["transaction_id"]
        for item in ranked
    ] == [2, 1]


def test_rag_ranking_rewards_description_overlap():
    from accounting_rag import (
        rank_accounting_examples,
    )

    candidates = [
        {
            "transaction_id": 10,
            "description": "Annual cloud software subscription",
            "vendor": None,
            "category": "Software",
        },
        {
            "transaction_id": 11,
            "description": "Cloud hosting",
            "vendor": None,
            "category": "Software",
        },
        {
            "transaction_id": 12,
            "description": "Office printer paper",
            "vendor": None,
            "category": "Office Supplies",
        },
    ]

    ranked = rank_accounting_examples(
        description="Annual cloud software subscription",
        vendor=None,
        candidates=candidates,
    )

    assert [
        item["transaction_id"]
        for item in ranked
    ] == [10, 11]


def test_rag_ranking_deduplicates_and_limits_results():
    from accounting_rag import (
        rank_accounting_examples,
    )

    candidates = [
        {
            "transaction_id": transaction_id,
            "description": "Software subscription",
            "vendor": "Microsoft",
            "category": "Software",
        }
        for transaction_id in range(1, 7)
    ]

    candidates.insert(
        1,
        dict(candidates[0]),
    )

    ranked = rank_accounting_examples(
        description="Software subscription",
        vendor="Microsoft",
        candidates=candidates,
        limit=5,
    )

    assert len(ranked) == 5
    assert [
        item["transaction_id"]
        for item in ranked
    ] == [1, 2, 3, 4, 5]


def test_rag_ranking_ignores_candidates_without_evidence():
    from accounting_rag import (
        rank_accounting_examples,
    )

    candidates = [
        {
            "transaction_id": 20,
            "description": "Office chairs",
            "vendor": "Furniture Store",
            "category": "Office Supplies",
        }
    ]

    ranked = rank_accounting_examples(
        description="Cloud hosting subscription",
        vendor="Microsoft",
        candidates=candidates,
    )

    assert ranked == []

def test_rag_trusted_history_uses_final_category_assignment(
    monkeypatch,
):
    import accounting_rag

    executions = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

        def execute(self, sql, binds=None):
            executions.append(
                (sql, binds or {})
            )

        def fetchall(self):
            sql = executions[-1][0]
            normalized = " ".join(
                sql.split()
            ).upper()

            if (
                "FROM ACCOUNTING_CATEGORIES" in normalized
                and "JOIN ACCOUNTING_CATEGORIES" not in normalized
            ):
                return [
                    (
                        3,
                        "6100",
                        "Software",
                        "EXPENSE",
                    )
                ]

            if ":VENDOR" in normalized:
                return [
                    (
                        10,
                        "Microsoft 365 subscription",
                        "Microsoft",
                        "Software",
                    )
                ]

            return []

    class FakeConnection:
        def __init__(self):
            self.closed = False

        def cursor(self):
            return FakeCursor()

        def close(self):
            self.closed = True

    connection = FakeConnection()

    monkeypatch.setattr(
        accounting_rag,
        "get_connection",
        lambda: connection,
    )

    context = accounting_rag.get_accounting_context(
        description=None,
        vendor="Microsoft",
    )

    assert context.examples == [
        {
            "transaction_id": 10,
            "description": "Microsoft 365 subscription",
            "vendor": "Microsoft",
            "category": "Software",
        }
    ]

    candidate_sql = next(
        sql
        for sql, binds in executions
        if "vendor" in binds
    )

    normalized = " ".join(
        candidate_sql.split()
    ).upper()

    assert (
        "JOIN ACCOUNTING_CATEGORIES AC"
        in normalized
    )
    assert (
        "FT.ACCOUNTING_CATEGORY_ID = "
        "AC.ACCOUNTING_CATEGORY_ID"
        in normalized
        or
        "AC.ACCOUNTING_CATEGORY_ID = "
        "FT.ACCOUNTING_CATEGORY_ID"
        in normalized
    )
    assert (
        "FT.ACCOUNTING_CATEGORY_ID IS NOT NULL"
        in normalized
    )
    assert "AC.IS_ACTIVE = 'Y'" in normalized

    # An AI suggestion alone is not the trust rule.
    assert "AI_SUGGESTED_CATEGORY" not in normalized
    assert "AI_CONFIDENCE" not in normalized

    # Do not fall back to the old legacy text rule.
    assert "CATEGORY IS NOT NULL" not in normalized

    assert connection.closed is True


def test_rag_trusted_history_description_query_uses_final_category(
    monkeypatch,
):
    import accounting_rag

    executions = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

        def execute(self, sql, binds=None):
            executions.append(
                (sql, binds or {})
            )

        def fetchall(self):
            sql = executions[-1][0]
            normalized = " ".join(
                sql.split()
            ).upper()

            if (
                "FROM ACCOUNTING_CATEGORIES" in normalized
                and "JOIN ACCOUNTING_CATEGORIES" not in normalized
            ):
                return [
                    (
                        3,
                        "6100",
                        "Software",
                        "EXPENSE",
                    )
                ]

            if ":KEYWORD" in normalized:
                return [
                    (
                        20,
                        "Annual cloud software subscription",
                        "Microsoft",
                        "Software",
                    )
                ]

            return []

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        accounting_rag,
        "get_connection",
        FakeConnection,
    )

    context = accounting_rag.get_accounting_context(
        description="Cloud software subscription",
        vendor=None,
    )

    assert [
        item["transaction_id"]
        for item in context.examples
    ] == [20]

    keyword_queries = [
        sql
        for sql, binds in executions
        if "keyword" in binds
    ]

    assert keyword_queries

    for sql in keyword_queries:
        normalized = " ".join(
            sql.split()
        ).upper()

        assert (
            "JOIN ACCOUNTING_CATEGORIES AC"
            in normalized
        )
        assert (
            "FT.ACCOUNTING_CATEGORY_ID IS NOT NULL"
            in normalized
        )
        assert (
            "AC.ACCOUNT_NAME"
            in normalized
        )
        assert (
            "AI_SUGGESTED_CATEGORY"
            not in normalized
        )

def test_rag_evidence_explanation_reports_deterministic_signals():
    from accounting_rag import (
        explain_accounting_example,
    )

    evidence = explain_accounting_example(
        description="Microsoft 365 subscription",
        vendor="Microsoft",
        example={
            "transaction_id": 10,
            "description": "Microsoft 365 subscription",
            "vendor": "Microsoft",
            "category": "Software",
        },
    )

    assert evidence["retrieval_score"] == 340
    assert evidence["match_reasons"] == [
        "EXACT_VENDOR",
        "EXACT_DESCRIPTION",
        "DESCRIPTION_TOKEN_OVERLAP",
    ]


def test_rag_evidence_summary_detects_category_conflict():
    from accounting_rag import (
        summarize_retrieved_accounting_evidence,
    )

    summary = summarize_retrieved_accounting_evidence(
        description="Microsoft 365 subscription",
        vendor="Microsoft",
        examples=[
            {
                "transaction_id": 10,
                "description": "Microsoft 365 subscription",
                "vendor": "Microsoft",
                "category": "Software",
            },
            {
                "transaction_id": 11,
                "description": "Microsoft office supplies",
                "vendor": "Microsoft",
                "category": "Office Supplies",
            },
        ],
    )

    assert summary["retrieved_categories"] == [
        "Office Supplies",
        "Software",
    ]
    assert summary["retrieved_category_conflict"] is True

    assert summary["historical_examples"][0][
        "retrieval_score"
    ] == 340
    assert "EXACT_VENDOR" in summary[
        "historical_examples"
    ][1]["match_reasons"]


def test_uncategorized_investigation_formatter_explains_rag_evidence():
    from ai_assistant import (
        _format_uncategorized_investigation,
    )

    result = {
        "transaction": {
            "transaction_id": 7,
            "transaction_date": "2026-09-01",
            "transaction_type": "EXPENSE",
            "description": "Microsoft 365 subscription",
            "amount": -120,
            "category": None,
            "vendor": "Microsoft",
            "reconciliation_status": "UNMATCHED",
            "status": "POSTED",
        },
        "investigation_status": "RECOMMENDATION_READY",
        "current_ai_suggestion": None,
        "evidence": {
            "available_categories": [
                "Software",
                "Office Supplies",
            ],
            "historical_examples": [
                {
                    "transaction_id": 10,
                    "description": "Microsoft 365 subscription",
                    "vendor": "Microsoft",
                    "category": "Software",
                    "retrieval_score": 340,
                    "match_reasons": [
                        "EXACT_VENDOR",
                        "EXACT_DESCRIPTION",
                        "DESCRIPTION_TOKEN_OVERLAP",
                    ],
                }
            ],
            "supporting_example_count": 1,
            "retrieved_categories": [
                "Office Supplies",
                "Software",
            ],
            "retrieved_category_conflict": True,
        },
        "recommendation": {
            "category": "Software",
            "confidence": 0.95,
            "high_confidence": True,
            "rationale": (
                "Retrieved history contains mixed evidence."
            ),
        },
        "requires_human_review": True,
    }

    message = _format_uncategorized_investigation(
        result
    )

    assert "retrieval score 340" in message
    assert "exact vendor" in message
    assert "exact description" in message
    assert "not AI confidence" in message
    assert (
        "historical examples span multiple categories"
        in message
    )
    assert "Office Supplies" in message
    assert "Software" in message
    assert "human review and approval" in message
