from dataclasses import dataclass

from database import get_connection


@dataclass
class AccountingContext:
    categories: list[dict]
    examples: list[dict]


def get_accounting_context(
    description: str | None,
    vendor: str | None,
) -> AccountingContext:
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    accounting_category_id,
                    account_code,
                    account_name,
                    account_type
                FROM accounting_categories
                WHERE is_active = 'Y'
                ORDER BY account_code
            """)

            categories = [
                {
                    "category_id": row[0],
                    "account_code": row[1],
                    "account_name": row[2],
                    "account_type": row[3],
                }
                for row in cursor.fetchall()
            ]

            examples: list[dict] = []
            seen_ids: set[int] = set()

            # 1. Vendor match gets highest priority.
            if vendor and vendor.strip():
                cursor.execute("""
                    SELECT
                        transaction_id,
                        description,
                        vendor,
                        category
                    FROM financial_transactions
                    WHERE category IS NOT NULL
                      AND vendor IS NOT NULL
                      AND LOWER(vendor) LIKE '%' || LOWER(:vendor) || '%'
                    ORDER BY transaction_id
                    FETCH FIRST 5 ROWS ONLY
                """, {
                    "vendor": vendor.strip(),
                })

                for row in cursor.fetchall():
                    example = {
                        "transaction_id": row[0],
                        "description": row[1],
                        "vendor": row[2],
                        "category": row[3],
                    }

                    examples.append(example)
                    seen_ids.add(row[0])

            # 2. Description keyword matches fill remaining slots.
            if description and len(examples) < 5:
                keywords = [
                    word.strip(".,-/()")
                    for word in description.split()
                    if len(word.strip(".,-/()")) >= 4
                ]

                for keyword in keywords:
                    if len(examples) >= 5:
                        break

                    cursor.execute("""
                        SELECT
                            transaction_id,
                            description,
                            vendor,
                            category
                        FROM financial_transactions
                        WHERE category IS NOT NULL
                          AND LOWER(description) LIKE '%' || LOWER(:keyword) || '%'
                        ORDER BY transaction_id
                        FETCH FIRST 5 ROWS ONLY
                    """, {
                        "keyword": keyword,
                    })

                    for row in cursor.fetchall():
                        if row[0] in seen_ids:
                            continue

                        examples.append({
                            "transaction_id": row[0],
                            "description": row[1],
                            "vendor": row[2],
                            "category": row[3],
                        })

                        seen_ids.add(row[0])

                        if len(examples) >= 5:
                            break

            return AccountingContext(
                categories=categories,
                examples=examples,
            )
    finally:
        connection.close()