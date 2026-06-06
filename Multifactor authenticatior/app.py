import os
import io
import time
import base64
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_bcrypt import Bcrypt
import pyotp
import qrcode

app = Flask(__name__)
# Cryptographically secure secret key for Flask sessions
app.secret_key = "secureauth_mfa_secret_key_987654321!"

# Enable bcrypt for password hashing
bcrypt = Bcrypt(app)

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    """Helper to open a database connection if not already open for the request context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Clean up database connection at the end of a request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database using the schema.sql definition script."""
    with app.app_context():
        db = get_db()
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
            print("Database successfully initialized from schema.")
        else:
            print("Warning: schema.sql file not found. Database could not be initialized.")

# Session Inactivity Timeout Middleware
@app.before_request
def check_session_timeout():
    """Enforces a 15-minute inactivity session timeout on authenticated routes."""
    # Exclude static assets from updating session activity
    if request.path.startswith('/static/'):
        return

    # Check if user is logged in
    if 'username' in session and 'user_id' in session:
        last_activity = session.get('last_activity')
        now = time.time()
        
        # Check if 15 minutes (900 seconds) have elapsed
        if last_activity and (now - last_activity > 900):
            session.clear()
            flash("Session expired due to inactivity. Please log in again.", "warning")
            return redirect(url_for('login', timeout=1))
        
        # Update last active time for the current request
        session['last_activity'] = now

# Audit Logging Helper
def log_activity(username, status):
    """Helper to record authentication attempts into the login_logs table."""
    db = get_db()
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    # Convert local IPv6 loopback to IPv4 equivalent for readability
    if ip_address == '::1':
        ip_address = '127.0.0.1'
        
    db.execute(
        "INSERT INTO login_logs (username, ip_address, status) VALUES (?, ?, ?)",
        (username, ip_address, status)
    )
    db.commit()

# --- ROUTES ---

@app.route("/")
def home():
    """Redirect root page to login or dashboard based on authentication state."""
    if 'username' in session and 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles new user accounts registration and initializes the MFA Setup phase."""
    if 'username' in session and 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password")
        
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        db = get_db()
        # Verify if username is already taken
        cursor = db.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            flash("Username is already taken. Choose a different one.", "danger")
            return render_template("register.html")

        # Hash password securely
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        # Generate pyotp random base32 seed secret
        secret_key = pyotp.random_base32()

        # Insert user with is_active = 0 (inactive until MFA Setup is verified)
        db.execute(
            "INSERT INTO users (username, email, password_hash, secret_key, is_active) VALUES (?, ?, ?, ?, 0)",
            (username, email, hashed_password, secret_key)
        )
        db.commit()

        # Set setup session state
        session['setup_mfa_username'] = username
        session['setup_mfa_email'] = email
        return redirect(url_for('setup_mfa'))

    return render_template("register.html")

@app.route("/setup-mfa", methods=["GET", "POST"])
def setup_mfa():
    """Generates the TOTP QR Code provisioning URI and verifies the first code to activate the user."""
    username = session.get('setup_mfa_username')
    email = session.get('setup_mfa_email')
    
    if not username:
        flash("Please register an account first.", "danger")
        return redirect(url_for('register'))

    db = get_db()
    # Fetch secret key
    user_row = db.execute("SELECT secret_key FROM users WHERE username = ?", (username,)).fetchone()
    if not user_row:
        return redirect(url_for('register'))
        
    secret_key = user_row['secret_key']

    if request.method == "POST":
        otp_code = request.form.get("otp_code", "").strip()
        
        totp = pyotp.TOTP(secret_key)
        # Verify code with a small window drift allowance of 30 seconds (valid_window=1)
        if totp.verify(otp_code, valid_window=1):
            # Activate user
            db.execute("UPDATE users SET is_active = 1 WHERE username = ?", (username,))
            db.commit()
            
            # Log registration setup success
            log_activity(username, "SUCCESS")
            
            session.pop('setup_mfa_username', None)
            session.pop('setup_mfa_email', None)
            flash("Account successfully created and MFA activated! Please sign in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid authentication code. Please check your app timer and re-enter.", "danger")

    # Generate QR Code image in memory (no disk footprint)
    totp = pyotp.TOTP(secret_key)
    provisioning_uri = totp.provisioning_uri(name=email, issuer_name="SecureAuth")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return render_template(
        "setup_mfa.html", 
        qr_code_base64=qr_code_base64, 
        secret_key=secret_key
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticates username and password and tracks account lockouts."""
    if 'username' in session and 'user_id' in session:
        return redirect(url_for('dashboard'))

    lockout_seconds = 0
    now = datetime.now()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user:
            # 1. Check account lockout state
            if user['lockout_until']:
                lockout_until = datetime.strptime(user['lockout_until'], '%Y-%m-%d %H:%M:%S')
                if now < lockout_until:
                    lockout_seconds = int((lockout_until - now).total_seconds())
                    log_activity(username, "LOCKED")
                    flash("This account is temporarily locked due to 3 failed attempts.", "locked")
                    return render_template("login.html", lockout_seconds=lockout_seconds)
                else:
                    # Lockout expired, reset lockout values in database
                    db.execute(
                        "UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE id = ?",
                        (user['id'],)
                    )
                    db.commit()
            
            # Ensure MFA setup was fully completed for this user
            if user['is_active'] == 0:
                # Redirect to complete registration setup
                session['setup_mfa_username'] = user['username']
                session['setup_mfa_email'] = user['email']
                flash("Please complete your MFA registration setup.", "warning")
                return redirect(url_for('setup_mfa'))

            # 2. Check password credentials
            if bcrypt.check_password_hash(user['password_hash'], password):
                # Credentials valid, move to factor 2 (TOTP)
                session['pre_mfa_username'] = username
                return redirect(url_for('verify'))
            else:
                # Password incorrect, increment attempts
                failed_attempts = user['failed_attempts'] + 1
                log_activity(username, "FAILED_PASSWORD")

                if failed_attempts >= 3:
                    # Trigger 5-minute lockout
                    lockout_time = (now + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
                    db.execute(
                        "UPDATE users SET failed_attempts = ?, lockout_until = ? WHERE id = ?",
                        (failed_attempts, lockout_time, user['id'])
                    )
                    db.commit()
                    flash("Account locked for 5 minutes due to 3 consecutive failed password attempts.", "locked")
                    lockout_seconds = 300
                else:
                    db.execute(
                        "UPDATE users SET failed_attempts = ? WHERE id = ?",
                        (failed_attempts, user['id'])
                    )
                    db.commit()
                    flash(f"Invalid credentials. Attempt {failed_attempts} of 3 before lockout.", "danger")
        else:
            # Generic message to prevent username enumeration
            flash("Invalid credentials.", "danger")

    return render_template("login.html", lockout_seconds=lockout_seconds)

@app.route("/verify", methods=["GET", "POST"])
def verify():
    """Handles secondary TOTP code challenge verification."""
    username = session.get('pre_mfa_username')
    if not username:
        return redirect(url_for('login'))

    if request.method == "POST":
        otp_code = request.form.get("otp_code", "").strip()

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user:
            totp = pyotp.TOTP(user['secret_key'])
            if totp.verify(otp_code, valid_window=1):
                # Reset failure count and lockout upon full successful login
                db.execute(
                    "UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE id = ?",
                    (user['id'],)
                )
                db.commit()
                
                # Audit log success
                log_activity(username, "SUCCESS")

                # Establish fully authorized user session
                session.pop('pre_mfa_username', None)
                session['user_id'] = user['id']
                session['username'] = username
                session['last_activity'] = time.time()
                
                return redirect(url_for('dashboard'))
            else:
                log_activity(username, "FAILED_OTP")
                flash("Invalid authentication code. Please check your authenticator timer.", "danger")

    return render_template("verify.html")

@app.route("/dashboard")
def dashboard():
    """Renders the central security audit dashboard."""
    if 'username' not in session or 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['username']
    db = get_db()

    # Get failed attempts for the indicator card
    user = db.execute("SELECT failed_attempts FROM users WHERE username = ?", (username,)).fetchone()
    failed_attempts = user['failed_attempts'] if user else 0

    # Fetch last 10 login activities
    logs_cursor = db.execute(
        "SELECT login_time, ip_address, status FROM login_logs WHERE username = ? ORDER BY login_time DESC LIMIT 10",
        (username,)
    )
    logs = logs_cursor.fetchall()

    # Determine "Last Login Time" (second most recent SUCCESS log, since most recent SUCCESS is the current login)
    last_login_cursor = db.execute(
        "SELECT login_time FROM login_logs WHERE username = ? AND status = 'SUCCESS' ORDER BY login_time DESC LIMIT 2",
        (username,)
    )
    last_logins = last_login_cursor.fetchall()
    
    last_login_time = None
    if len(last_logins) > 1:
        last_login_time = last_logins[1]['login_time']
    elif len(last_logins) == 1:
        last_login_time = "First session recorded"

    # Dynamic Risk Level assessment based on failed attempts and logs
    risk_level = "LOW"
    recent_failures = db.execute(
        "SELECT COUNT(*) as count FROM login_logs WHERE username = ? AND status != 'SUCCESS' AND login_time > datetime('now', '-15 minutes')",
        (username,)
    ).fetchone()['count']

    if failed_attempts >= 3 or recent_failures >= 3:
        risk_level = "HIGH"
    elif failed_attempts > 0 or recent_failures > 0:
        risk_level = "MEDIUM"

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip == '::1':
        client_ip = '127.0.0.1'

    return render_template(
        "dashboard.html",
        logs=logs,
        failed_attempts=failed_attempts,
        last_login_time=last_login_time,
        risk_level=risk_level,
        client_ip=client_ip
    )

@app.route("/logout")
def logout():
    """Logs out the user and clears session values."""
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for('login'))

if __name__ == "__main__":
    # Pre-initialize SQLite DB schema tables
    init_db()
    
    # Run the server on debug mode, port 5000
    app.run(debug=True, port=5000)
