-- ============================================================
-- E-COMMERCE INTELLIGENCE PLATFORM
-- PL/SQL BUSINESS LOGIC
-- Oracle Database 26ai
-- ============================================================


-- ============================================================
-- 1. CUSTOMER LIFETIME VALUE
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_customer_lifetime_value (
    p_customer_id IN customers.customer_id%TYPE
)
RETURN NUMBER
IS
    v_lifetime_value NUMBER;
BEGIN
    SELECT NVL(SUM(oi.quantity * oi.unit_price), 0)
    INTO v_lifetime_value
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.customer_id = p_customer_id
      AND o.status = 'COMPLETED';

    RETURN v_lifetime_value;
END;
/


-- ============================================================
-- 2. CUSTOMER SEGMENT
-- ============================================================

CREATE OR REPLACE FUNCTION get_customer_segment (
    p_customer_id IN customers.customer_id%TYPE
)
RETURN VARCHAR2
IS
    v_clv NUMBER;
BEGIN
    v_clv := calculate_customer_lifetime_value(p_customer_id);

    IF v_clv < 500 THEN
        RETURN 'BRONZE';
    ELSIF v_clv <= 1500 THEN
        RETURN 'SILVER';
    ELSE
        RETURN 'GOLD';
    END IF;
END;
/


-- ============================================================
-- 3. UPDATE PRODUCT STOCK
-- ============================================================

CREATE OR REPLACE PROCEDURE update_product_stock (
    p_product_id    IN products.product_id%TYPE,
    p_quantity_sold IN NUMBER
)
IS
    v_current_stock products.stock_quantity%TYPE;
BEGIN
    SELECT stock_quantity
    INTO v_current_stock
    FROM products
    WHERE product_id = p_product_id;

    IF p_quantity_sold <= 0 THEN
        RAISE_APPLICATION_ERROR(
            -20001,
            'Quantity sold must be greater than 0.'
        );

    ELSIF p_quantity_sold > v_current_stock THEN
        RAISE_APPLICATION_ERROR(
            -20002,
            'Insufficient stock.'
        );

    ELSE
        UPDATE products
        SET stock_quantity = stock_quantity - p_quantity_sold
        WHERE product_id = p_product_id;
    END IF;

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(
            -20003,
            'Product not found.'
        );
END;
/


-- ============================================================
-- 4. PROCESS ORDER
-- ============================================================

CREATE OR REPLACE PROCEDURE process_order (
    p_order_id IN orders.order_id%TYPE
)
IS
    v_order_status orders.status%TYPE;
BEGIN
    SELECT status
    INTO v_order_status
    FROM orders
    WHERE order_id = p_order_id;

    IF v_order_status = 'COMPLETED' THEN
        RAISE_APPLICATION_ERROR(
            -20004,
            'Order is already completed.'
        );

    ELSIF v_order_status = 'CANCELLED' THEN
        RAISE_APPLICATION_ERROR(
            -20005,
            'Cannot process a cancelled order.'
        );
    END IF;

    SAVEPOINT before_order_processing;

    FOR item IN (
        SELECT product_id, quantity
        FROM order_items
        WHERE order_id = p_order_id
    )
    LOOP
        update_product_stock(
            item.product_id,
            item.quantity
        );
    END LOOP;

    UPDATE orders
    SET status = 'COMPLETED'
    WHERE order_id = p_order_id;

    COMMIT;

EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO before_order_processing;
        RAISE;
END;
/


-- ============================================================
-- 5. E-COMMERCE PACKAGE SPECIFICATION
-- ============================================================

CREATE OR REPLACE PACKAGE ecommerce_pkg AS

    FUNCTION calculate_customer_lifetime_value (
        p_customer_id IN customers.customer_id%TYPE
    ) RETURN NUMBER;

    FUNCTION get_customer_segment (
        p_customer_id IN customers.customer_id%TYPE
    ) RETURN VARCHAR2;

    PROCEDURE update_product_stock (
        p_product_id    IN products.product_id%TYPE,
        p_quantity_sold IN NUMBER
    );

    PROCEDURE process_order (
        p_order_id IN orders.order_id%TYPE
    );

END ecommerce_pkg;
/


-- ============================================================
-- 6. E-COMMERCE PACKAGE BODY
-- ============================================================

CREATE OR REPLACE PACKAGE BODY ecommerce_pkg AS

    FUNCTION calculate_customer_lifetime_value (
        p_customer_id IN customers.customer_id%TYPE
    ) RETURN NUMBER
    IS
        v_lifetime_value NUMBER;
    BEGIN
        SELECT NVL(SUM(oi.quantity * oi.unit_price), 0)
        INTO v_lifetime_value
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        WHERE o.customer_id = p_customer_id
          AND o.status = 'COMPLETED';

        RETURN v_lifetime_value;
    END;


    FUNCTION get_customer_segment (
        p_customer_id IN customers.customer_id%TYPE
    ) RETURN VARCHAR2
    IS
        v_clv NUMBER;
    BEGIN
        v_clv := calculate_customer_lifetime_value(p_customer_id);

        IF v_clv < 500 THEN
            RETURN 'BRONZE';
        ELSIF v_clv <= 1500 THEN
            RETURN 'SILVER';
        ELSE
            RETURN 'GOLD';
        END IF;
    END;


    PROCEDURE update_product_stock (
        p_product_id    IN products.product_id%TYPE,
        p_quantity_sold IN NUMBER
    )
    IS
        v_current_stock products.stock_quantity%TYPE;
    BEGIN
        SELECT stock_quantity
        INTO v_current_stock
        FROM products
        WHERE product_id = p_product_id;

        IF p_quantity_sold <= 0 THEN
            RAISE_APPLICATION_ERROR(
                -20001,
                'Quantity sold must be greater than 0.'
            );

        ELSIF p_quantity_sold > v_current_stock THEN
            RAISE_APPLICATION_ERROR(
                -20002,
                'Insufficient stock.'
            );

        ELSE
            UPDATE products
            SET stock_quantity = stock_quantity - p_quantity_sold
            WHERE product_id = p_product_id;
        END IF;

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(
                -20003,
                'Product not found.'
            );
    END;


    PROCEDURE process_order (
        p_order_id IN orders.order_id%TYPE
    )
    IS
        v_order_status orders.status%TYPE;
    BEGIN
        SELECT status
        INTO v_order_status
        FROM orders
        WHERE order_id = p_order_id;

        IF v_order_status = 'COMPLETED' THEN
            RAISE_APPLICATION_ERROR(
                -20004,
                'Order is already completed.'
            );

        ELSIF v_order_status = 'CANCELLED' THEN
            RAISE_APPLICATION_ERROR(
                -20005,
                'Cannot process a cancelled order.'
            );
        END IF;

        SAVEPOINT before_order_processing;

        FOR item IN (
            SELECT product_id, quantity
            FROM order_items
            WHERE order_id = p_order_id
        )
        LOOP
            update_product_stock(
                item.product_id,
                item.quantity
            );
        END LOOP;

        UPDATE orders
        SET status = 'COMPLETED'
        WHERE order_id = p_order_id;

        COMMIT;

    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK TO before_order_processing;
            RAISE;
    END;

END ecommerce_pkg;
/


-- ============================================================
-- 7. PRODUCTS LAST UPDATED TRIGGER
-- ============================================================

CREATE OR REPLACE TRIGGER trg_products_last_updated
BEFORE UPDATE ON products
FOR EACH ROW
BEGIN
    :NEW.last_updated := SYSDATE;
END;
/