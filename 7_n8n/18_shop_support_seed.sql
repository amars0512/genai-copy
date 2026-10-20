-- Seed data for workflow 18 (customer-support agent: RAG + MCP).
-- Creates/refreshes ONLY the shop_* tables in the `n8n` database; touches nothing else.
-- Dates are relative to today, so the refund-window scenarios stay valid whenever you run the demo.
--
-- Run (Docker):
--   docker exec -i mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < 7_n8n/18_shop_support_seed.sql
--
-- Scenario per order (see 18_README.md):
--   ORD1024 delivered 12 days ago            -> ELIGIBLE for refund (30-day window)
--   ORD1025 delivered 45 days ago            -> NOT eligible (window over)
--   ORD1026 shipped, in transit              -> not delivered yet, cancel/refund after delivery
--   ORD1027 delivered, refund APPROVED       -> show check_refund_status
--   ORD1028 electronics, delivered, opened   -> NOT eligible (opened electronics: warranty only)
--   ORD1029 delivered 5 days ago, refund REQUESTED (pending)
--   ORD1030 processing (not shipped)         -> can still be cancelled for full refund
--   ORD1031 delivered 29 days ago            -> eligible, last day tomorrow (edge case)

CREATE DATABASE IF NOT EXISTS n8n;
USE n8n;

DROP TABLE IF EXISTS shop_refunds;
DROP TABLE IF EXISTS shop_orders;
DROP TABLE IF EXISTS shop_customers;

CREATE TABLE shop_customers (
    customer_id   VARCHAR(10) PRIMARY KEY,
    name          VARCHAR(80)  NOT NULL,
    city          VARCHAR(60)  NOT NULL,
    loyalty_tier  VARCHAR(20)  NOT NULL,
    member_since  DATE         NOT NULL
);

CREATE TABLE shop_orders (
    order_id       VARCHAR(10) PRIMARY KEY,
    customer_id    VARCHAR(10)  NOT NULL,
    item           VARCHAR(100) NOT NULL,
    category       VARCHAR(30)  NOT NULL,
    amount_inr     DECIMAL(10,2) NOT NULL,
    status         VARCHAR(20)  NOT NULL,      -- processing | shipped | delivered | cancelled
    package_opened BOOLEAN      NOT NULL DEFAULT FALSE,
    ordered_on     DATE         NOT NULL,
    delivered_on   DATE         NULL,
    courier        VARCHAR(40)  NULL,
    tracking_no    VARCHAR(30)  NULL,
    FOREIGN KEY (customer_id) REFERENCES shop_customers(customer_id)
);

CREATE TABLE shop_refunds (
    refund_id      VARCHAR(10) PRIMARY KEY,
    order_id       VARCHAR(10)  NOT NULL,
    requested_on   DATE         NOT NULL,
    reason         VARCHAR(120) NOT NULL,
    status         VARCHAR(20)  NOT NULL,      -- requested | approved | rejected | paid
    amount_inr     DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES shop_orders(order_id)
);

INSERT INTO shop_customers VALUES
 ('CUST01', 'Ravi Sharma',   'Pune',      'Gold',   CURDATE() - INTERVAL 900 DAY),
 ('CUST02', 'Priya Nair',    'Kochi',     'Silver', CURDATE() - INTERVAL 400 DAY),
 ('CUST03', 'Amit Verma',    'Delhi',     'Basic',  CURDATE() - INTERVAL 60 DAY),
 ('CUST04', 'Sneha Kulkarni','Mumbai',    'Gold',   CURDATE() - INTERVAL 1500 DAY),
 ('CUST05', 'Farhan Sheikh', 'Bengaluru', 'Silver', CURDATE() - INTERVAL 250 DAY);

INSERT INTO shop_orders VALUES
 ('ORD1024','CUST01','Wireless Headphones',     'Electronics', 3499.00,'delivered',FALSE,CURDATE() - INTERVAL 16 DAY,CURDATE() - INTERVAL 12 DAY,'BlueDart','BD7781024'),
 ('ORD1025','CUST02','Cotton Bedsheet Set',     'Home',        1899.00,'delivered',TRUE, CURDATE() - INTERVAL 50 DAY,CURDATE() - INTERVAL 45 DAY,'Delhivery','DL5521025'),
 ('ORD1026','CUST03','Running Shoes',           'Footwear',    2799.00,'shipped',  FALSE,CURDATE() - INTERVAL 3 DAY, NULL,                     'Ekart','EK9901026'),
 ('ORD1027','CUST01','Ceramic Dinner Set',      'Home',        4250.00,'delivered',TRUE, CURDATE() - INTERVAL 20 DAY,CURDATE() - INTERVAL 17 DAY,'BlueDart','BD7781027'),
 ('ORD1028','CUST04','Bluetooth Speaker',       'Electronics', 2299.00,'delivered',TRUE, CURDATE() - INTERVAL 10 DAY,CURDATE() - INTERVAL 7 DAY, 'Delhivery','DL5521028'),
 ('ORD1029','CUST05','Denim Jacket',            'Clothing',    2599.00,'delivered',TRUE, CURDATE() - INTERVAL 9 DAY, CURDATE() - INTERVAL 5 DAY, 'Ekart','EK9901029'),
 ('ORD1030','CUST02','Stainless Steel Bottle',  'Kitchen',      699.00,'processing',FALSE,CURDATE() - INTERVAL 1 DAY, NULL,                    NULL, NULL),
 ('ORD1031','CUST04','Yoga Mat',                'Fitness',     1199.00,'delivered',FALSE, CURDATE() - INTERVAL 33 DAY,CURDATE() - INTERVAL 29 DAY,'BlueDart','BD7781031');

INSERT INTO shop_refunds VALUES
 ('REF501','ORD1027',CURDATE() - INTERVAL 10 DAY,'Two plates arrived cracked','approved',4250.00),
 ('REF502','ORD1029',CURDATE() - INTERVAL 2 DAY, 'Size too small',            'requested',2599.00),
 ('REF503','ORD1025',CURDATE() - INTERVAL 30 DAY,'Colour different from photo','rejected',1899.00);

SELECT 'shop_customers' AS tbl, COUNT(*) AS n_rows FROM shop_customers
UNION ALL SELECT 'shop_orders', COUNT(*) FROM shop_orders
UNION ALL SELECT 'shop_refunds', COUNT(*) FROM shop_refunds;
