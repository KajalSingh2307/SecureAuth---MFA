# SecureAuth MFA: Google Authenticator Clone for Multi-Factor Authentication

A complete, standalone cybersecurity demonstration project that showcases **Time-Based One-Time Password (TOTP) Multi-Factor Authentication** integrated with brute-force protection, activity audit logging, and a premium glassmorphic security dashboard.

---

## Key Cybersecurity Features Demonstrated

1. **Defense-in-Depth Authentication**: Combines knowledge-based authentication (Username/Password) with ownership-based authentication (physical possession of a registered TOTP authenticator device).
2. **Cryptographically Secure Shared Secrets**: Utilizes a randomized 32-character base32 secret seed (`pyotp`) mapped to each individual user account.
3. **QR Code Provisioning (RFC 6238)**: Automatically constructs an standard `otpauth://` URI and compiles it into an SVG/PNG QR Code entirely in memory, eliminating the risk of temporary files containing secrets being cached on disk.
4. **Brute-Force Protection (Account Lockout)**: Tracks consecutive failed login attempts. If a user inputs an incorrect password 3 times, their account is locked for **5 minutes**.
5. **Inactivity Session Expiry**: Monitors active session time; automatically invalidates user credentials and logs them out after **15 minutes** of absolute inactivity. Includes a floating UI warning widget showing time remaining.
6. **Detailed Audit trail (Access Logs)**: Records timestamp, client IP address, and result state (`MFA_VERIFIED`, `PWD_INCORRECT`, `TOTP_INVALID`, `ACC_LOCKED`) for every authentication request.
7. **Bcrypt Password Hashing**: Utilizes salt-hashed representations of passwords to prevent plain-text exposure in database leaks.
8. **Dynamic Risk Assessment**: Evaluates log logs and failed login thresholds to categorize current account risk as **LOW**, **MEDIUM**, or **HIGH** in real-time.

---

## Tech Stack & Dependencies

- **Backend**: Python Flask
- **Database**: SQLite3
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism layout, animations, layouts), JavaScript
- **Libraries**:
  - `Flask` & `Flask-Bcrypt` (Web framework and password hashing)
  - `pyotp` (TOTP generation and verification)
  - `qrcode` & `pillow` (QR code generation in base64 strings)

---

## Database Design

The database contains two core tables initialized automatically via `schema.sql`:

### `users`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | Auto-incrementing identifier. |
| `username` | TEXT (Unique) | Unique user identification. |
| `email` | TEXT | User's contact email. |
| `password_hash`| TEXT | Bcrypt salt-hashed password string. |
| `secret_key` | TEXT | Unique Base32 secret key used for generating user-specific TOTP. |
| `is_active` | INTEGER | Active flag (0 = unverified, 1 = verified/active). |
| `failed_attempts`| INTEGER | Number of consecutive failed attempts since last success. |
| `lockout_until` | TEXT | ISO Timestamp until which the account remains locked (if applicable). |
| `created_at` | TIMESTAMP | Time of account creation. |

### `login_logs`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | Auto-incrementing log entry ID. |
| `username` | TEXT | Target user credential attempted. |
| `login_time` | TIMESTAMP | Automatic timestamp of the access event. |
| `ip_address` | TEXT | Client IPv4 or IPv6 address. |
| `status` | TEXT | Log state (`SUCCESS`, `FAILED_PASSWORD`, `FAILED_OTP`, `LOCKED`). |

---

## Visual Design Aesthetics

The interface is customized with a **Glassmorphism Dark Theme**:
- Deep radial space background (`#090d16` to `#111827`) with blurred accent flows.
- Translucent frosted glass login, registration, and confirmation cards utilizing `backdrop-filter: blur(20px)` and subtle glowing borders.
- Interactive multi-digit OTP inputs that automatically shift cursor focus on typing and support direct clipboard paste integration.
- Responsive, grid-based layout for desktop and mobile displays.

---

## Step-by-Step Installation

### 1. Pre-requisites
Make sure you have **Python 3** installed on your system.

### 2. Install Packages
Run the following command to download and install the required modules:
```bash
pip install Flask Flask-Bcrypt pyotp qrcode pillow
```

### 3. Start the Web Server
Launch the application by running:
```bash
python app.py
```
Upon startup, the server automatically reads `schema.sql` and generates `database.db` inside the project folder.

### 4. Open in Browser
Open your browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Demonstration Walkthrough (For Faculty Review)

Follow this path to demonstrate all integrated cybersecurity concepts:

### Phase 1: Registration & Provisioning
1. Click **Register Now** on the login page.
2. Create an account with a new Username, Email, and Password.
3. Click **Continue to MFA Setup**. You will be redirected to the setup wizard.
4. **MFA Provisioning**:
   - Open **Google Authenticator** (or any TOTP app) on your mobile device.
   - Scan the QR code, or manually input the provided **Base32 secret key**.
   - Input the generated 6-digit code into the split input fields.
   - Click **Verify and Complete Setup**. The user state `is_active` changes to `1` in the database.

### Phase 2: Lockout Demonstration (Brute-Force Defense)
1. Navigate back to the **Login** screen.
2. Enter the registered username but type an **incorrect password**.
   - Notice the system displays: `Invalid credentials. Attempt 1 of 3 before lockout.`
3. Enter an incorrect password a second time.
   - Notice the status counter increases.
4. Enter an incorrect password a third time.
   - The card input disables immediately and displays: `Account locked for 5 minutes due to 3 consecutive failed password attempts.`
   - A real-time timer countdown displays when inputs will reactivate.

### Phase 3: Successful Authentication Flow
1. Once the cooldown timer finishes (or delete the user/manually reset `failed_attempts` in SQLite to skip), enter the **correct** username and password.
2. You will pass Factor 1 and be redirected to the **MFA Verification** screen.
3. Enter the active 6-digit code from your authenticator app.
   - Notice how inputs auto-focus next fields and support backspaces.
4. Click **Verify and Login** to access the Dashboard.

### Phase 4: Security Dashboard & Session Inactivity
1. Review the dynamic metrics:
   - Current Client IP address.
   - Failed attempts count.
   - Last successful login timestamp (reflecting prior logins).
   - Real-time logs detailing successful/failed logins, incorrect passcodes, and lockouts.
2. Inspect the **Risk Assessment Gauge** (displays LOW risk, or MEDIUM/HIGH if failures occurred recently).
3. Observe the floating **Session Inactivity** widget on the bottom right. It counts down from 15 minutes. 
   - If left inactive, the page redirects automatically back to the login screen showing a session expired warning.
