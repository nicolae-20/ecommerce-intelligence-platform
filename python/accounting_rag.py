from dataclasses import dataclass
import re

from database import get_connection


MAX_CONTEXT_EXAMPLES = 5

DESCRIPTION_STOP_WORDS = frozenset({
    "and",
    "for",
    "from",
    "into",
    "onto",
    "our",
    "that",
    "the",
    "these",
    "this",
    "those",
    "with",
    "your",
})


@dataclass
class AccountingContext:
    categories: list[dict]
    examples: list[dict]


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(
        re.findall(
            r"[a-z0-9]+",
            value.casefold(),
        )
    )


def _description_tokens(
    value: str | None,
) -> tuple[str, ...]:
    normalized = _normalize_text(value)

    if not normalized:
        return ()

    tokens = []

    for token in normalized.split():
        if len(token) < 3:
            continue

        if token in DESCRIPTION_STOP_WORDS:
            continue

        if token not in tokens:
            tokens.append(token)

    return tuple(tokens)


def _evaluate_accounting_example(
    description: str | None,
    vendor: str | None,
    example: dict,
) -> tuple[int, list[str]]:
    score = 0
    match_reasons: list[str] = []

    query_vendor = _normalize_text(vendor)
    example_vendor = _normalize_text(
        example.get("vendor")
    )

    if query_vendor and example_vendor:
        if query_vendor == example_vendor:
            score += 200
            match_reasons.append("EXACT_VENDOR")
        elif (
            query_vendor in example_vendor
            or example_vendor in query_vendor
        ):
            score += 120
            match_reasons.append("PARTIAL_VENDOR")

    query_description = _normalize_text(
        description
    )
    example_description = _normalize_text(
        example.get("description")
    )

    if (
        query_description
        and example_description
        and query_description == example_description
    ):
        score += 50
        match_reasons.append("EXACT_DESCRIPTION")

    query_tokens = set(
        _description_tokens(description)
    )
    example_tokens = set(
        _description_tokens(
            example.get("description")
        )
    )

    overlap = query_tokens & example_tokens

    if overlap:
        score += len(overlap) * 20
        match_reasons.append(
            "DESCRIPTION_TOKEN_OVERLAP"
        )

        if query_tokens:
            overlap_ratio = (
                len(overlap)
                / len(query_tokens)
            )
            score += round(
                overlap_ratio * 30
            )

    return score, match_reasons


def explain_accounting_example(
    description: str | None,
    vendor: str | None,
    example: dict,
) -> dict:
    score, match_reasons = (
        _evaluate_accounting_example(
            description=description,
            vendor=vendor,
            example=example,
        )
    )

    return {
        "retrieval_score": score,
        "match_reasons": match_reasons,
    }


def _score_accounting_example(
    description: str | None,
    vendor: str | None,
    example: dict,
) -> int:
    return explain_accounting_example(
        description=description,
        vendor=vendor,
        example=example,
    )["retrieval_score"]


def summarize_retrieved_accounting_evidence(
    description: str | None,
    vendor: str | None,
    examples: list[dict],
) -> dict:
    historical_examples = []
    retrieved_categories: set[str] = set()

    for example in examples:
        enriched_example = dict(example)

        enriched_example.update(
            explain_accounting_example(
                description=description,
                vendor=vendor,
                example=example,
            )
        )

        historical_examples.append(
            enriched_example
        )

        category = example.get("category")

        if category:
            retrieved_categories.add(category)

    categories = sorted(retrieved_categories)

    return {
        "historical_examples": historical_examples,
        "retrieved_categories": categories,
        "retrieved_category_conflict": (
            len(categories) > 1
        ),
    }


def rank_accounting_examples(
    description: str | None,
    vendor: str | None,
    candidates: list[dict],
    limit: int = MAX_CONTEXT_EXAMPLES,
) -> list[dict]:
    if limit <= 0:
        return []

    scored_examples = []
    seen_ids: set[int] = set()

    for candidate in candidates:
        transaction_id = candidate.get(
            "transaction_id"
        )

        if not isinstance(transaction_id, int):
            continue

        if transaction_id in seen_ids:
            continue

        seen_ids.add(transaction_id)

        score = _score_accounting_example(
            description=description,
            vendor=vendor,
            example=candidate,
        )

        if score <= 0:
            continue

        scored_examples.append(
            (
                score,
                transaction_id,
                candidate,
            )
        )

    scored_examples.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    return [
        dict(candidate)
        for _, _, candidate
        in scored_examples[:limit]
    ]


def get_accounting_context(
    description: str | None,
    vendor: str | None,
    exclude_transaction_id: int | None = None,
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

            candidates: list[dict] = []
            candidate_ids: set[int] = set()

            def add_candidates(rows):
                for row in rows:
                    transaction_id = row[0]

                    if transaction_id in candidate_ids:
                        continue

                    candidate_ids.add(
                        transaction_id
                    )

                    candidates.append({
                        "transaction_id": row[0],
                        "description": row[1],
                        "vendor": row[2],
                        "category": row[3],
                    })

            # Vendor candidates remain important, but they
            # no longer automatically consume all five
            # final context slots.
            if vendor and vendor.strip():
                vendor_exclusion = ""
                vendor_binds = {"vendor": vendor.strip()}

                if exclude_transaction_id is not None:
                    vendor_exclusion = """
                      AND ft.transaction_id != :exclude_transaction_id
                    """
                    vendor_binds["exclude_transaction_id"] = (
                        exclude_transaction_id
                    )

                cursor.execute("""
                    SELECT
                        ft.transaction_id,
                        ft.description,
                        ft.vendor,
                        ac.account_name
                    FROM financial_transactions ft
                    JOIN accounting_categories ac
                      ON ac.accounting_category_id =
                         ft.accounting_category_id
                     AND ac.is_active = 'Y'
                    WHERE ft.accounting_category_id IS NOT NULL
                      AND ft.vendor IS NOT NULL
                      AND LOWER(ft.vendor)
                          LIKE '%' || LOWER(:vendor) || '%'
                      {vendor_exclusion}
                    ORDER BY ft.transaction_id
                    FETCH FIRST 20 ROWS ONLY
                """.format(vendor_exclusion=vendor_exclusion), vendor_binds)

                add_candidates(
                    cursor.fetchall()
                )

            # Gather a broader deterministic candidate set
            # from meaningful description tokens.
            for keyword in _description_tokens(
                description
            ):
                description_exclusion = ""
                description_binds = {"keyword": keyword}

                if exclude_transaction_id is not None:
                    description_exclusion = """
                      AND ft.transaction_id != :exclude_transaction_id
                    """
                    description_binds["exclude_transaction_id"] = (
                        exclude_transaction_id
                    )

                cursor.execute("""
                    SELECT
                        ft.transaction_id,
                        ft.description,
                        ft.vendor,
                        ac.account_name
                    FROM financial_transactions ft
                    JOIN accounting_categories ac
                      ON ac.accounting_category_id =
                         ft.accounting_category_id
                     AND ac.is_active = 'Y'
                    WHERE ft.accounting_category_id IS NOT NULL
                      AND ft.description IS NOT NULL
                      AND LOWER(ft.description)
                          LIKE '%' || LOWER(:keyword) || '%'
                      {description_exclusion}
                    ORDER BY ft.transaction_id
                    FETCH FIRST 20 ROWS ONLY
                """.format(
                    description_exclusion=description_exclusion,
                ), description_binds)

                add_candidates(
                    cursor.fetchall()
                )

            examples = rank_accounting_examples(
                description=description,
                vendor=vendor,
                candidates=candidates,
                limit=MAX_CONTEXT_EXAMPLES,
            )

            return AccountingContext(
                categories=categories,
                examples=examples,
            )
    finally:
        connection.close()
