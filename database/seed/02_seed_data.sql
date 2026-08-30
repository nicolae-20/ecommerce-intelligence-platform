-- ============================================================
-- E-COMMERCE INTELLIGENCE PLATFORM
-- SEED DATA
-- Oracle Database 26ai
-- ============================================================


-- ============================================================
-- 1. CATEGORIES
-- ============================================================

INSERT INTO categories (category_name)
VALUES ('Electronics');

INSERT INTO categories (category_name)
VALUES ('Clothing');

INSERT INTO categories (category_name)
VALUES ('Books');

INSERT INTO categories (category_name)
VALUES ('Sports');

INSERT INTO categories (category_name)
VALUES ('Home and Kitchen');


-- ============================================================
-- 2. DEPARTMENTS
-- ============================================================

INSERT INTO departments (department_name)
VALUES ('Sales');

INSERT INTO departments (department_name)
VALUES ('Customer Support');

INSERT INTO departments (department_name)
VALUES ('IT');

INSERT INTO departments (department_name)
VALUES ('Finance');


-- ============================================================
-- 3. SUPPLIERS
-- ============================================================

INSERT INTO suppliers (supplier_name, country, contact_email)
VALUES (
    'TechSource Europe',
    'Germany',
    'contact@techsource.eu'
);

INSERT INTO suppliers (supplier_name, country, contact_email)
VALUES (
    'Global Electronics',
    'USA',
    'sales@globalelectronics.com'
);

INSERT INTO suppliers (supplier_name, country, contact_email)
VALUES (
    'BookWorld',
    'UK',
    'orders@bookworld.co.uk'
);

INSERT INTO suppliers (supplier_name, country, contact_email)
VALUES (
    'HomeStyle Supplies',
    'Poland',
    'contact@homestyle.pl'
);

INSERT INTO suppliers (supplier_name, country, contact_email)
VALUES (
    'SportGear Direct',
    'Netherlands',
    'sales@sportgear.nl'
);


-- ============================================================
-- 4. CUSTOMERS
-- ============================================================

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'Andrei',
    'Popescu',
    'andrei@example.com',
    'Romania',
    24
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'Maria',
    'Ionescu',
    'maria@example.com',
    'Romania',
    31
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'John',
    'Smith',
    'john@example.com',
    'USA',
    28
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'Sofia',
    'Miller',
    'sofia@example.com',
    'UK',
    22
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'David',
    'Brown',
    'david@example.com',
    'USA',
    35
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'Elena',
    'Pop',
    'elena@example.com',
    'Romania',
    27
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'Alex',
    'Wilson',
    'alex@example.com',
    'Canada',
    41
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'Laura',
    'Clark',
    'laura@example.com',
    'UK',
    29
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'Daniel',
    'Marin',
    'daniel@example.com',
    'Romania',
    38
);

INSERT INTO customers (
    first_name,
    last_name,
    email,
    country,
    age
)
VALUES (
    'Emma',
    'Taylor',
    'emma@example.com',
    'USA',
    26
);


-- ============================================================
-- 5. PRODUCTS
-- ============================================================

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'iPhone 15',
    1,
    1,
    899.99,
    600,
    15
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'Samsung Galaxy S24',
    1,
    2,
    799.99,
    520,
    25
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'Sony WH-1000XM5',
    1,
    1,
    349.99,
    220,
    40
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'Nike Air Max',
    2,
    5,
    129.99,
    70,
    42
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'Levi''s 501 Jeans',
    2,
    4,
    89.99,
    45,
    30
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'Clean Code',
    3,
    3,
    44.99,
    20,
    60
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'SQL Pocket Guide',
    3,
    3,
    29.99,
    12,
    100
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'KitchenAid Mixer',
    5,
    4,
    299.99,
    180,
    18
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'Yoga Mat',
    4,
    5,
    35.99,
    15,
    75
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'Dumbbells Set',
    4,
    5,
    79.99,
    35,
    25
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'T-Shirt Classic',
    2,
    4,
    24.99,
    10,
    100
);

INSERT INTO products (
    product_name,
    category_id,
    supplier_id,
    price,
    cost_price,
    stock_quantity
)
VALUES (
    'Football',
    4,
    5,
    79.99,
    40,
    40
);


-- ============================================================
-- 6. ORDERS
-- ============================================================

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    1,
    DATE '2026-01-05',
    'COMPLETED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    2,
    DATE '2026-01-08',
    'COMPLETED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    3,
    DATE '2026-01-12',
    'SHIPPED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    1,
    DATE '2026-01-20',
    'COMPLETED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    5,
    DATE '2026-02-02',
    'PENDING'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    6,
    DATE '2026-02-10',
    'COMPLETED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    4,
    DATE '2026-02-15',
    'CANCELLED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    7,
    DATE '2026-02-18',
    'SHIPPED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    8,
    DATE '2026-02-20',
    'COMPLETED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    10,
    DATE '2026-03-01',
    'COMPLETED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    3,
    DATE '2026-03-05',
    'COMPLETED'
);

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
VALUES (
    9,
    DATE '2026-03-10',
    'PENDING'
);


-- ============================================================
-- 7. ORDER_ITEMS
-- ============================================================

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    1,
    1,
    1,
    899.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    1,
    2,
    2,
    799.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    2,
    6,
    1,
    44.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    2,
    7,
    2,
    29.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    3,
    3,
    1,
    349.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    3,
    9,
    1,
    35.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    4,
    8,
    1,
    299.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    4,
    10,
    2,
    79.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    5,
    5,
    1,
    89.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    6,
    4,
    1,
    129.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    6,
    9,
    2,
    35.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    7,
    12,
    1,
    79.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    8,
    11,
    3,
    24.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    8,
    4,
    1,
    129.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    9,
    2,
    1,
    799.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    9,
    3,
    1,
    349.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    10,
    1,
    1,
    899.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    10,
    3,
    1,
    349.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    11,
    5,
    2,
    89.99
);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
VALUES (
    12,
    8,
    1,
    299.99
);


-- ============================================================
-- 8. PAYMENTS
-- ============================================================

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    1,
    DATE '2026-01-05',
    2499.97,
    'CARD',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    2,
    DATE '2026-01-08',
    104.97,
    'PAYPAL',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    3,
    DATE '2026-01-12',
    385.98,
    'CARD',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    4,
    DATE '2026-01-20',
    459.97,
    'CARD',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    5,
    DATE '2026-02-02',
    89.99,
    'PAYPAL',
    'PENDING'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    6,
    DATE '2026-02-10',
    201.97,
    'CARD',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    7,
    DATE '2026-02-15',
    79.99,
    'CARD',
    'REFUNDED'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    8,
    DATE '2026-02-18',
    204.96,
    'PAYPAL',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    9,
    DATE '2026-02-20',
    1149.98,
    'CARD',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    10,
    DATE '2026-03-01',
    1249.98,
    'CARD',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    11,
    DATE '2026-03-05',
    179.98,
    'BANK_TRANSFER',
    'PAID'
);

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    payment_method,
    payment_status
)
VALUES (
    12,
    DATE '2026-03-10',
    299.99,
    'PAYPAL',
    'PENDING'
);


-- ============================================================
-- 9. REVIEWS
-- ============================================================

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    1,
    1,
    5,
    'Excellent phone and very fast.',
    DATE '2026-01-10'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    2,
    4,
    4,
    'Good product for the price.',
    DATE '2026-01-12'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    3,
    3,
    5,
    'Amazing headphones.',
    DATE '2026-01-18'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    4,
    8,
    4,
    'Very useful in the kitchen.',
    DATE '2026-01-25'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    5,
    5,
    3,
    'Good quality but expensive.',
    DATE '2026-02-05'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    6,
    9,
    5,
    'Very comfortable.',
    DATE '2026-02-12'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    7,
    10,
    4,
    'Solid set of dumbbells.',
    DATE '2026-02-20'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    8,
    11,
    5,
    'Great t-shirt.',
    DATE '2026-02-25'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    9,
    2,
    4,
    'Good phone, works well.',
    DATE '2026-02-26'
);

INSERT INTO reviews (
    customer_id,
    product_id,
    rating,
    review_text,
    review_date
)
VALUES (
    10,
    7,
    4,
    'Very useful guide.',
    DATE '2026-03-03'
);


-- ============================================================
-- 10. DISCOUNTS
-- ============================================================

INSERT INTO discounts (
    product_id,
    discount_percent,
    start_date,
    end_date
)
VALUES (
    1,
    10,
    DATE '2026-01-01',
    DATE '2026-01-31'
);

INSERT INTO discounts (
    product_id,
    discount_percent,
    start_date,
    end_date
)
VALUES (
    2,
    15,
    DATE '2026-02-01',
    DATE '2026-02-15'
);

INSERT INTO discounts (
    product_id,
    discount_percent,
    start_date,
    end_date
)
VALUES (
    4,
    20,
    DATE '2026-01-15',
    DATE '2026-02-15'
);

INSERT INTO discounts (
    product_id,
    discount_percent,
    start_date,
    end_date
)
VALUES (
    6,
    10,
    DATE '2026-02-01',
    DATE '2026-02-28'
);

INSERT INTO discounts (
    product_id,
    discount_percent,
    start_date,
    end_date
)
VALUES (
    8,
    25,
    DATE '2026-02-01',
    DATE '2026-02-28'
);

INSERT INTO discounts (
    product_id,
    discount_percent,
    start_date,
    end_date
)
VALUES (
    11,
    30,
    DATE '2026-03-01',
    DATE '2026-03-31'
);


-- ============================================================
-- 11. EMPLOYEES
-- ============================================================

INSERT INTO employees (
    first_name,
    last_name,
    department_id,
    manager_id,
    hire_date,
    salary
)
VALUES (
    'Michael',
    'Johnson',
    3,
    NULL,
    DATE '2021-03-15',
    85000
);

INSERT INTO employees (
    first_name,
    last_name,
    department_id,
    manager_id,
    hire_date,
    salary
)
VALUES (
    'Sarah',
    'Williams',
    1,
    NULL,
    DATE '2020-07-01',
    78000
);

INSERT INTO employees (
    first_name,
    last_name,
    department_id,
    manager_id,
    hire_date,
    salary
)
VALUES (
    'Robert',
    'Davis',
    4,
    NULL,
    DATE '2019-11-10',
    82000
);

INSERT INTO employees (
    first_name,
    last_name,
    department_id,
    manager_id,
    hire_date,
    salary
)
VALUES (
    'Lisa',
    'Brown',
    2,
    NULL,
    DATE '2022-01-20',
    65000
);

INSERT INTO employees (
    first_name,
    last_name,
    department_id,
    manager_id,
    hire_date,
    salary
)
VALUES (
    'Daniel',
    'Wilson',
    3,
    1,
    DATE '2023-02-10',
    62000
);

INSERT INTO employees (
    first_name,
    last_name,
    department_id,
    manager_id,
    hire_date,
    salary
)
VALUES (
    'Emma',
    'Taylor',
    1,
    2,
    DATE '2023-04-05',
    59000
);

INSERT INTO employees (
    first_name,
    last_name,
    department_id,
    manager_id,
    hire_date,
    salary
)
VALUES (
    'James',
    'Anderson',
    4,
    3,
    DATE '2024-01-15',
    61000
);

INSERT INTO employees (
    first_name,
    last_name,
    department_id,
    manager_id,
    hire_date,
    salary
)
VALUES (
    'Olivia',
    'Thomas',
    2,
    4,
    DATE '2024-03-01',
    52000
);


-- ============================================================
-- FINAL COMMIT
-- ============================================================

COMMIT;