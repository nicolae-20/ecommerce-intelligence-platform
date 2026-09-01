from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_top_customers():
    response = client.get("/customers/top")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 5
    assert data[0]["customer_name"] == "Andrei Popescu"


def test_monthly_revenue():
    response = client.get("/analytics/monthly-revenue")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3
    assert data[0]["order_month"] == "2026-01"


def test_customer_metrics():
    response = client.get("/customers/metrics")

    assert response.status_code == 200

    data = response.json()

    assert len(data) > 0
    assert data[0]["customer_id"] == 1


def test_profit_by_category():
    response = client.get("/analytics/profit-by-category")

    assert response.status_code == 200

    data = response.json()

    assert len(data) > 0
    assert "category_name" in data[0]
    assert "revenue" in data[0]
    assert "cost" in data[0]
    assert "profit" in data[0]

def test_overview():
    response = client.get("/analytics/overview")

    assert response.status_code == 200

    data = response.json()

    assert data["total_revenue"] > 0
    assert data["total_orders"] > 0
    assert data["total_customers"] > 0
    assert data["average_order_value"] > 0


def test_financial_summary():
    response = client.get("/analytics/financial-summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_revenue"] == 6236.8
    assert data["total_cogs"] == 3909.0
    assert data["gross_profit"] == 2327.8
    assert data["gross_margin"] == 37.32


def test_bookkeeping_summary():
    response = client.get("/bookkeeping/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_revenue"] == 950.0
    assert data["total_expenses"] == 228.5
    assert data["net_movement"] == 721.5
    assert data["transactions_requiring_review"] == 3



def test_review_queue():
    response = client.get("/bookkeeping/review-queue")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    assert data[0]["transaction_id"] == 1
    assert data[0]["ai_suggested_category"] == "Software"
    assert data[0]["ai_confidence"] == 0.97

    assert data[1]["transaction_id"] == 4
    assert data[1]["ai_suggested_category"] == "Bank Fees"
    assert data[1]["ai_confidence"] == 0.99

    assert data[2]["transaction_id"] == 5
    assert data[2]["ai_suggested_category"] == "Software"
    assert data[2]["ai_confidence"] == 0.95


def test_approve_transaction():
    response = client.post("/bookkeeping/transactions/1/approve")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "AI category suggestion approved successfully."

    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE financial_transactions
                SET
                    category = NULL,
                    reconciliation_status = 'UNMATCHED'
                WHERE transaction_id = 1
            """)

            connection.commit()
    finally:
        connection.close()

def test_reject_transaction():
    response = client.post("/bookkeeping/transactions/1/reject")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "AI category suggestion rejected."

    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
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


def test_assign_transaction_category():
    response = client.post("/bookkeeping/transactions/1/category/1")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "Transaction category assigned successfully."

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


def test_cancel_reject():
    from database import get_connection

    # Simulate a rejected AI suggestion first.
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE financial_transactions
                SET
                    ai_suggested_category = NULL,
                    ai_confidence = NULL
                WHERE transaction_id = 1
            """)

            connection.commit()
    finally:
        connection.close()

    response = client.post(
        "/bookkeeping/transactions/1/cancel-reject"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "AI category suggestion restored."

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
    finally:
        connection.close()



def test_reconciliation_review():
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

    from analytics import run_reconciliation

    result = run_reconciliation()

    assert result is True

    response = client.get("/bookkeeping/reconciliation-review")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    items_by_type = {
        item["match_type"]: item
        for item in data
    }

    possible_match = items_by_type["POSSIBLE_MATCH"]

    assert possible_match["bank_transaction_id"] == 4
    assert possible_match["status"] == "UNMATCHED"
    assert possible_match["financial_transaction_id"] == 5
    assert possible_match["match_confidence"] == 0.9
    assert possible_match["system_description"] == "Microsoft 365"

    no_match = items_by_type["NO_MATCH"]

    assert no_match["bank_transaction_id"] == 3
    assert no_match["status"] == "UNMATCHED"
    assert no_match["financial_transaction_id"] is None
    assert no_match["match_confidence"] == 0
    assert no_match["system_description"] is None

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


def test_confirm_reconciliation():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = 5,
                    match_type = 'POSSIBLE_MATCH',
                    match_confidence = 0.90
                WHERE bank_transaction_id = 4
            """)

            connection.commit()
    finally:
        connection.close()

    response = client.post(
        "/bookkeeping/reconciliation/4/confirm"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == (
        "Reconciliation match confirmed successfully."
    )

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
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL,
                    match_type = NULL,
                    match_confidence = NULL
                WHERE bank_transaction_id = 4
            """)

            connection.commit()
    finally:
        connection.close()


def test_reject_reconciliation():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = 5,
                    match_type = 'POSSIBLE_MATCH',
                    match_confidence = 0.90
                WHERE bank_transaction_id = 4
            """)

            connection.commit()
    finally:
        connection.close()

    response = client.post(
        "/bookkeeping/reconciliation/4/reject"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == (
        "Reconciliation match rejected successfully."
    )

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
                UPDATE bank_transactions
                SET
                    status = 'UNMATCHED',
                    financial_transaction_id = NULL,
                    match_type = NULL,
                    match_confidence = NULL
                WHERE bank_transaction_id = 4
            """)

            connection.commit()
    finally:
        connection.close()


def test_investigate_reconciliation():
    from database import get_connection

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
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

    response = client.post(
        "/bookkeeping/reconciliation/3/investigate"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == (
        "Bank transaction marked as investigated."
    )

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

            # Restore demo state.
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

            connection.commit()
    finally:
        connection.close()