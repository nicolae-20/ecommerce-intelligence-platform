-- Oracle Accounting Bootstrap Demo Seed
-- Fresh schema only. Identity values are produced by insertion order.

INSERT INTO accounting_categories (
    account_code,
    account_name,
    account_type,
    is_active
) VALUES ('4000', 'Sales Revenue', 'REVENUE', 'Y');

INSERT INTO accounting_categories (
    account_code,
    account_name,
    account_type,
    is_active
) VALUES ('5000', 'Cost of Goods Sold', 'COGS', 'Y');

INSERT INTO accounting_categories (
    account_code,
    account_name,
    account_type,
    is_active
) VALUES ('6100', 'Software', 'EXPENSE', 'Y');

INSERT INTO accounting_categories (
    account_code,
    account_name,
    account_type,
    is_active
) VALUES ('6200', 'Office Supplies', 'EXPENSE', 'Y');

INSERT INTO accounting_categories (
    account_code,
    account_name,
    account_type,
    is_active
) VALUES ('6300', 'Bank Fees', 'EXPENSE', 'Y');

INSERT INTO accounting_categories (
    account_code,
    account_name,
    account_type,
    is_active
) VALUES ('6400', 'Travel', 'EXPENSE', 'Y');

INSERT INTO accounting_categories (
    account_code,
    account_name,
    account_type,
    is_active
) VALUES ('6500', 'Advertising', 'EXPENSE', 'Y');

INSERT INTO accounting_categories (
    account_code,
    account_name,
    account_type,
    is_active
) VALUES ('6600', 'Utilities', 'EXPENSE', 'Y');


INSERT INTO financial_transactions (
    transaction_date,
    transaction_type,
    description,
    amount,
    category,
    vendor,
    status,
    ai_suggested_category,
    ai_confidence,
    reconciliation_status,
    original_ai_category,
    original_ai_confidence,
    accounting_category_id
) VALUES (
    DATE '2024-01-05',
    'EXPENSE',
    'Cloud hosting subscription',
    -129.00,
    NULL,
    'Cloud Services',
    'POSTED',
    'Software',
    0.97,
    'UNMATCHED',
    'Software',
    0.97,
    NULL
);

INSERT INTO financial_transactions (
    transaction_date,
    transaction_type,
    description,
    amount,
    category,
    vendor,
    status,
    ai_suggested_category,
    ai_confidence,
    reconciliation_status,
    accounting_category_id
) VALUES (
    DATE '2024-01-10',
    'EXPENSE',
    'Office supply order',
    -96.00,
    'Office Supplies',
    'Office Store',
    'POSTED',
    NULL,
    NULL,
    'MATCHED',
    4
);

INSERT INTO financial_transactions (
    transaction_date,
    transaction_type,
    description,
    amount,
    category,
    vendor,
    status,
    ai_suggested_category,
    ai_confidence,
    reconciliation_status,
    accounting_category_id
) VALUES (
    DATE '2024-01-15',
    'SALE',
    'Online store sale',
    950.00,
    'Sales Revenue',
    'Demo Storefront',
    'POSTED',
    NULL,
    NULL,
    'MATCHED',
    1
);

INSERT INTO financial_transactions (
    transaction_date,
    transaction_type,
    description,
    amount,
    category,
    vendor,
    status,
    ai_suggested_category,
    ai_confidence,
    reconciliation_status,
    accounting_category_id
) VALUES (
    DATE '2024-01-20',
    'BANK_FEE',
    'Monthly bank service fee',
    -3.50,
    NULL,
    'Demo Bank',
    'POSTED',
    'Bank Fees',
    0.99,
    'UNMATCHED',
    NULL
);

INSERT INTO financial_transactions (
    transaction_date,
    transaction_type,
    description,
    amount,
    category,
    vendor,
    status,
    ai_suggested_category,
    ai_confidence,
    reconciliation_status,
    accounting_category_id
) VALUES (
    DATE '2024-01-25',
    'EXPENSE',
    'Microsoft 365',
    -12.00,
    NULL,
    'Microsoft',
    'PENDING',
    'Software',
    0.95,
    'UNMATCHED',
    NULL
);


INSERT INTO bank_transactions (
    transaction_date,
    description,
    amount,
    reference_number
) VALUES (
    DATE '2024-01-15',
    'Demo sale settlement',
    950.00,
    'DEMO-BANK-001'
);

INSERT INTO bank_transactions (
    transaction_date,
    description,
    amount,
    reference_number
) VALUES (
    DATE '2024-01-05',
    'Cloud subscription debit',
    -129.00,
    'DEMO-BANK-002'
);

INSERT INTO bank_transactions (
    transaction_date,
    description,
    amount,
    reference_number
) VALUES (
    DATE '2024-01-18',
    'Unidentified demo debit',
    -48.00,
    'DEMO-BANK-003'
);

INSERT INTO bank_transactions (
    transaction_date,
    description,
    amount,
    reference_number
) VALUES (
    DATE '2024-01-26',
    'Microsoft subscription debit',
    -12.00,
    'DEMO-BANK-004'
);


COMMIT;
