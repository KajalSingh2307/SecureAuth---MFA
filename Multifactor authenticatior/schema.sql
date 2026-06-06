-- Schema for SecureAuth MFA

-- Table to store user details and security states
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    secret_key TEXT NOT NULL,
    is_active INTEGER DEFAULT 0, -- 0 = registered but MFA not set up yet, 1 = MFA fully verified
    failed_attempts INTEGER DEFAULT 0,
    lockout_until TEXT NULL, -- Timestamp until which the user is locked out
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store access and audit logs for logins
CREATE TABLE IF NOT EXISTS login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    status TEXT NOT NULL -- 'SUCCESS', 'FAILED_PASSWORD', 'FAILED_OTP', 'LOCKED'
);
