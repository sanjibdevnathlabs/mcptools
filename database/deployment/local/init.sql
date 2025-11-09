-- Initialize MCP Database for local development
-- This script runs automatically when MySQL container starts

-- Create test database if not exists
CREATE DATABASE IF NOT EXISTS mcp_db;
CREATE DATABASE IF NOT EXISTS mcp_test_db;

-- Use the main database
USE mcp_db;

-- Create sample users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create sample products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (email, name) VALUES 
    ('alice@example.com', 'Alice Smith'),
    ('bob@example.com', 'Bob Johnson'),
    ('charlie@example.com', 'Charlie Brown')
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO products (name, description, price, stock) VALUES
    ('Laptop', 'High-performance laptop', 1299.99, 10),
    ('Mouse', 'Wireless mouse', 29.99, 50),
    ('Keyboard', 'Mechanical keyboard', 79.99, 25)
ON DUPLICATE KEY UPDATE name=name;

-- Grant permissions
GRANT ALL PRIVILEGES ON mcp_db.* TO 'mcp_user'@'%';
GRANT ALL PRIVILEGES ON mcp_test_db.* TO 'mcp_user'@'%';
FLUSH PRIVILEGES;

-- Show initialization status
SELECT 'Database initialized successfully!' AS status;
SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS product_count FROM products;

