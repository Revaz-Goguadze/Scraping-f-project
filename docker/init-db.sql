-- E-Commerce Price Monitoring System - PostgreSQL Initialization Script
-- This script sets up the database for the containerized application

-- Create database (if not exists)
-- CREATE DATABASE price_monitor;

-- Switch to the application database
\c price_monitor;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create initial application user with proper permissions
-- (The main user is created via environment variables)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE price_monitor TO price_monitor_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO price_monitor_user;

-- Set up performance optimizations for the database
ALTER DATABASE price_monitor SET timezone TO 'UTC';
ALTER DATABASE price_monitor SET log_statement TO 'none';
ALTER DATABASE price_monitor SET log_min_duration_statement TO 1000;

-- Create indexes for better performance (will be created by SQLAlchemy)
-- The application will create the actual tables via SQLAlchemy migrations

-- Log initialization completion
INSERT INTO pg_catalog.pg_settings (name, setting) 
VALUES ('log_line_prefix', '# Price Monitor DB initialized successfully at ' || now());

-- Note: The actual table creation will be handled by the application
-- using SQLAlchemy models when the application starts. 