-- Initialize Test Database for Integration Tests
-- This script creates the test database schema and sample data
-- Works with any database name (test_db locally, mcp_db in Docker)

-- Create test databases if not exists
CREATE DATABASE IF NOT EXISTS test_db;
CREATE DATABASE IF NOT EXISTS mcp_db;
CREATE DATABASE IF NOT EXISTS test_mcp_db;

-- Use the database from environment or test_db as default
-- This line will be overridden by the calling context
USE test_db;

-- Drop existing tables for clean state
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

-- Create users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    INDEX idx_email (email),
    INDEX idx_status (status),
    INDEX idx_deleted_at (deleted_at)
);

-- Create products table
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category)
);

-- Insert test users
INSERT INTO users (email, name, status) VALUES 
    ('test1@example.com', 'Test User 1', 'active'),
    ('test2@example.com', 'Test User 2', 'active'),
    ('test3@example.com', 'Test User 3', 'inactive'),
    ('alice@example.com', 'Alice Smith', 'active'),
    ('bob@example.com', 'Bob Johnson', 'active');

-- Insert test products
INSERT INTO products (name, description, price, stock, category) VALUES
    ('Laptop', 'High-performance laptop', 1299.99, 10, 'Electronics'),
    ('Mouse', 'Wireless mouse', 29.99, 50, 'Accessories'),
    ('Keyboard', 'Mechanical keyboard', 79.99, 25, 'Accessories'),
    ('Monitor', '27-inch 4K monitor', 399.99, 15, 'Electronics'),
    ('Headphones', 'Noise-cancelling headphones', 199.99, 30, 'Audio');

-- Populate test_mcp_db with same schema (for tests expecting this database)
USE test_mcp_db;

-- Drop existing tables for clean state
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

-- Create users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    INDEX idx_email (email),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create products table
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    category VARCHAR(100),
    INDEX idx_name (name),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert test users into test_mcp_db
INSERT INTO users (email, name, status) VALUES
    ('alice@example.com', 'Alice Smith', 'active'),
    ('bob@example.com', 'Bob Johnson', 'active'),
    ('charlie@example.com', 'Charlie Brown', 'inactive');

-- Insert test products into test_mcp_db
INSERT INTO products (name, description, price, stock, category) VALUES
    ('Laptop', 'High-performance laptop', 1299.99, 10, 'Electronics'),
    ('Mouse', 'Wireless mouse', 29.99, 50, 'Accessories'),
    ('Keyboard', 'Mechanical keyboard', 79.99, 25, 'Accessories'),
    ('Monitor', '27-inch 4K monitor', 399.99, 15, 'Electronics'),
    ('Headphones', 'Noise-cancelling headphones', 199.99, 30, 'Audio');

-- Switch back to test_db
USE test_db;

-- Verify initialization
SELECT 'Test databases initialized successfully!' AS status;
SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS product_count FROM products;

