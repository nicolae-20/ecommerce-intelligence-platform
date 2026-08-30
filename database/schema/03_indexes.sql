-- ============================================================
-- E-COMMERCE INTELLIGENCE PLATFORM
-- INDEXES
-- Oracle Database 26ai
-- ============================================================

CREATE INDEX idx_orders_customer
ON orders(customer_id);

CREATE INDEX idx_orders_status
ON orders(status);

CREATE INDEX idx_orders_order_date
ON orders(order_date);

CREATE INDEX idx_order_items_order
ON order_items(order_id);

CREATE INDEX idx_order_items_product
ON order_items(product_id);

CREATE INDEX idx_products_category
ON products(category_id);

CREATE INDEX idx_products_supplier
ON products(supplier_id);

CREATE INDEX idx_reviews_product
ON reviews(product_id);