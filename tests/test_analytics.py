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
    get_financial_summary,
    get_monthly_revenue,
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
    assert "get_reconciliation_review" in TOOL_REGISTRY
    assert "get_audit_log" in TOOL_REGISTRY

    assert callable(TOOL_REGISTRY["get_bookkeeping_summary"])
    assert callable(TOOL_REGISTRY["get_ai_review_queue"])
    assert callable(TOOL_REGISTRY["get_reconciliation_review"])
    assert callable(TOOL_REGISTRY["get_audit_log"])


def test_ai_tool_definitions():
    from ai_tools import TOOL_DEFINITIONS

    names = {
        tool["name"]
        for tool in TOOL_DEFINITIONS
    }

    assert names == {
        "get_bookkeeping_summary",
        "get_ai_review_queue",
        "get_reconciliation_review",
        "get_audit_log",
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
    assert "category" in transaction_tool["parameters"]["properties"]
    assert "vendor" in transaction_tool["parameters"]["properties"]
    assert "transaction_type" in transaction_tool["parameters"]["properties"]
    assert "reconciliation_status" in transaction_tool["parameters"]["properties"]
    assert "categorization_state" in transaction_tool["parameters"]["properties"]
    assert "min_amount" in transaction_tool["parameters"]["properties"]
    assert "max_amount" in transaction_tool["parameters"]["properties"]
    assert "status" in transaction_tool["parameters"]["properties"]

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
        "Show me transactions from August."
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


def test_tool_get_transactions_binds_optional_filters(monkeypatch):
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
        vendor="office depot",
        transaction_type="EXPENSE",
        reconciliation_status="MATCHED",
        categorization_state="CATEGORIZED",
    )

    assert result == []
    assert ":vendor" in captured["statement"]
    assert ":transaction_type" in captured["statement"]
    assert ":reconciliation_status" in captured["statement"]
    assert ":categorization_state" in captured["statement"]
    assert "office depot" not in captured["statement"]
    assert "EXPENSE" not in captured["statement"]
    assert "MATCHED" not in captured["statement"]
    assert captured["parameters"]["vendor"] == "office depot"
    assert captured["parameters"]["transaction_type"] == "EXPENSE"
    assert captured["parameters"]["reconciliation_status"] == "MATCHED"
    assert captured["parameters"]["categorization_state"] == "CATEGORIZED"
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
