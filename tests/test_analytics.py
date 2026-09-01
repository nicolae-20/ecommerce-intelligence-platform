import sys
from pathlib import Path

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