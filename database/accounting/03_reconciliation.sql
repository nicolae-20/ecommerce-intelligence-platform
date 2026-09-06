-- Oracle Accounting Bootstrap Reconciliation Procedure
-- This preserves the current live procedure behavior without redesign.

CREATE OR REPLACE PROCEDURE reconcile_bank_transactions
AS
BEGIN
    FOR bank_tx IN (
        SELECT
            bank_transaction_id,
            transaction_date,
            amount
        FROM bank_transactions
        WHERE status = 'UNMATCHED'
    )
    LOOP
        UPDATE bank_transactions bt
        SET
            financial_transaction_id = (
                SELECT MIN(ft.transaction_id)
                FROM financial_transactions ft
                WHERE ft.amount = bank_tx.amount
                  AND ABS(ft.transaction_date - bank_tx.transaction_date) <= 2
            ),

            match_type = CASE
                WHEN (
                    SELECT COUNT(*)
                    FROM financial_transactions ft
                    WHERE ft.amount = bank_tx.amount
                      AND ABS(ft.transaction_date - bank_tx.transaction_date) <= 2
                ) = 0
                    THEN 'NO_MATCH'

                WHEN (
                    SELECT COUNT(*)
                    FROM financial_transactions ft
                    WHERE ft.amount = bank_tx.amount
                      AND ABS(ft.transaction_date - bank_tx.transaction_date) <= 2
                ) = 1
                    AND (
                        SELECT MIN(ft.transaction_date)
                        FROM financial_transactions ft
                        WHERE ft.amount = bank_tx.amount
                          AND ABS(ft.transaction_date - bank_tx.transaction_date) <= 2
                    ) = bank_tx.transaction_date
                    THEN 'EXACT_MATCH'

                WHEN (
                    SELECT COUNT(*)
                    FROM financial_transactions ft
                    WHERE ft.amount = bank_tx.amount
                      AND ABS(ft.transaction_date - bank_tx.transaction_date) <= 2
                ) = 1
                    THEN 'POSSIBLE_MATCH'

                ELSE 'NO_MATCH'
            END,

            match_confidence = CASE
                WHEN (
                    SELECT COUNT(*)
                    FROM financial_transactions ft
                    WHERE ft.amount = bank_tx.amount
                      AND ABS(ft.transaction_date - bank_tx.transaction_date) <= 2
                ) = 0
                    THEN 0

                WHEN (
                    SELECT COUNT(*)
                    FROM financial_transactions ft
                    WHERE ft.amount = bank_tx.amount
                      AND ft.transaction_date = bank_tx.transaction_date
                ) = 1
                    THEN 1.00

                WHEN (
                    SELECT COUNT(*)
                    FROM financial_transactions ft
                    WHERE ft.amount = bank_tx.amount
                      AND ABS(ft.transaction_date - bank_tx.transaction_date) = 1
                ) = 1
                    THEN 0.90

                WHEN (
                    SELECT COUNT(*)
                    FROM financial_transactions ft
                    WHERE ft.amount = bank_tx.amount
                      AND ABS(ft.transaction_date - bank_tx.transaction_date) = 2
                ) = 1
                    THEN 0.80

                ELSE 0
            END,

            status = CASE
                WHEN (
                    SELECT COUNT(*)
                    FROM financial_transactions ft
                    WHERE ft.amount = bank_tx.amount
                      AND ft.transaction_date = bank_tx.transaction_date
                ) = 1
                    THEN 'MATCHED'
                ELSE 'UNMATCHED'
            END

        WHERE bt.bank_transaction_id = bank_tx.bank_transaction_id;
    END LOOP;

    COMMIT;
END;
/
