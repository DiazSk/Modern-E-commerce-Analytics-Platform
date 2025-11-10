-- ============================================
-- Modern E-Commerce Analytics Platform
-- PostgreSQL Source Database Initialization
-- ============================================
-- This script creates tables for the e-commerce source system
-- It runs automatically when the postgres-source container starts
-- ============================================

-- ==========================================
-- DROP EXISTING TABLES (For Clean Start)
-- ==========================================
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- ==========================================
-- CUSTOMERS TABLE
-- ==========================================
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    registration_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- For SCD Type 2 tracking
    customer_segment VARCHAR(20) NOT NULL DEFAULT 'bronze',
    segment_start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    segment_end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_segment CHECK (customer_segment IN ('bronze', 'silver', 'gold', 'platinum')),
    CONSTRAINT chk_dates CHECK (segment_end_date IS NULL OR segment_end_date > segment_start_date)
);

-- Create indexes for performance
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_segment ON customers(customer_segment);
CREATE INDEX idx_customers_is_current ON customers(is_current);
CREATE INDEX idx_customers_registration_date ON customers(registration_date);

-- ==========================================
-- ORDERS TABLE
-- ==========================================
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    order_total DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    shipping_address TEXT,
    order_status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_order_total CHECK (order_total >= 0),
    CONSTRAINT chk_payment_method CHECK (payment_method IN ('credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay')),
    CONSTRAINT chk_order_status CHECK (order_status IN ('pending', 'processing', 'completed', 'cancelled', 'returned'))
);

-- Create indexes for performance
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_date_customer ON orders(order_date, customer_id);  -- Composite index for common queries

-- ==========================================
-- ORDER_ITEMS TABLE (Line Items)
-- ==========================================
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,  -- References external product catalog (from API)
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,

    -- Calculated field (for convenience)
    line_total DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price - discount_amount) STORED,

    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_quantity CHECK (quantity > 0),
    CONSTRAINT chk_unit_price CHECK (unit_price >= 0),
    CONSTRAINT chk_discount CHECK (discount_amount >= 0 AND discount_amount <= (quantity * unit_price))
);

-- Create indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- ==========================================
-- TRIGGER: Update updated_at timestamp
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to customers
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to orders
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- SAMPLE DATA (For Testing Connection)
-- ==========================================
-- Insert one customer for testing
INSERT INTO customers (email, first_name, last_name, phone, customer_segment)
VALUES ('test@example.com', 'Test', 'User', '555-0100', 'silver');

-- Insert one order for testing
INSERT INTO orders (customer_id, order_total, payment_method, order_status, shipping_address)
VALUES (1, 99.99, 'credit_card', 'completed', '123 Test St, Test City, TC 12345');

-- Insert order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_amount)
VALUES
    (1, 1, 2, 39.99, 5.00),
    (1, 2, 1, 24.99, 0.00);

-- ==========================================
-- VERIFICATION QUERIES
-- ==========================================
-- These run automatically to verify setup
SELECT 'Database initialized successfully!' AS status;
SELECT COUNT(*) AS customer_count FROM customers;
SELECT COUNT(*) AS order_count FROM orders;
SELECT COUNT(*) AS order_item_count FROM order_items;

-- ==========================================
-- USEFUL VIEWS FOR ANALYTICS
-- ==========================================

-- View: Complete order details with customer info
CREATE OR REPLACE VIEW vw_order_details AS
SELECT
    o.order_id,
    o.order_date,
    c.customer_id,
    c.email,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.customer_segment,
    oi.order_item_id,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.discount_amount,
    oi.line_total,
    o.order_total,
    o.payment_method,
    o.order_status
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id;

-- View: Customer summary statistics
CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
    c.customer_id,
    c.email,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.customer_segment,
    c.registration_date,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(o.order_total), 0) AS total_spent,
    COALESCE(AVG(o.order_total), 0) AS avg_order_value,
    MAX(o.order_date) AS last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE c.is_current = TRUE
GROUP BY c.customer_id, c.email, c.first_name, c.last_name, c.customer_segment, c.registration_date;

-- ==========================================
-- GRANT PERMISSIONS
-- ==========================================
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ecommerce_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ecommerce_user;

-- ==========================================
-- COMPLETION MESSAGE
-- ==========================================
SELECT
    'PostgreSQL source database setup complete!' AS message,
    'Tables created: customers, orders, order_items' AS tables,
    'Views created: vw_order_details, vw_customer_summary' AS views,
    'Sample data inserted: 1 customer, 1 order, 2 items' AS sample_data;
