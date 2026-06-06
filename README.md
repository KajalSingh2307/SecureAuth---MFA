**SecureAuth MFA**

A secure web-based Multi-Factor Authentication (MFA) system developed using Python Flask and SQLite. The application enhances traditional username-password authentication by integrating Time-Based One-Time Password (TOTP) verification through Google Authenticator.
This project demonstrates practical cybersecurity concepts such as secure password storage, multi-factor authentication, brute-force protection, session management, and audit logging.

**Features**
> User Registration & Login
> Password Hashing using Bcrypt
> Multi-Factor Authentication (MFA)
> Google Authenticator Integration
> TOTP-Based OTP Verification
> Brute-Force Attack Protection
> Account Lockout Mechanism
> Session Timeout Management
> Login Activity Monitoring

**Tech Stack**
Backend - Python,Flask
Database - SQLite
Security Libraries - Flask-Bcrypt, PyOTP
Frontend - HTML, CSS, JavaScript
Authentication - Google Authenticator

**System Workflow**
1. User registers an account.
2. Password is securely hashed using Bcrypt.
3. A unique TOTP secret key is generated.
4. QR Code is created for Google Authenticator setup.
5. User scans the QR Code using Google Authenticator.
   
**During login:**
Username and password are verified.
User enters a time-based OTP.
Access is granted only after successful verification of both factors.
Login activities are recorded in audit logs.

**Security Features**
1. **Password Encryption** - Passwords are hashed using Bcrypt before storage.
2. **Multi-Factor Authentication** - OTP verification is implemented using TOTP, generating a new code every 30 seconds.
3. **Brute-Force Protection** - Accounts are temporarily locked after multiple failed login attempts.
4. **Session Timeout**- Inactive sessions automatically expire after a predefined duration.
5. **Audit Logging**
All login attempts are tracked with:
Username
Timestamp
IP Address
Login Status

**Future Enhancements**

1. Biometric Authentication
2. Email/SMS OTP Support
3. AI-Based Threat Detection
4. Mobile Application Support
5. Admin Dashboard
6. Cloud Deployment (AWS/Azure)
