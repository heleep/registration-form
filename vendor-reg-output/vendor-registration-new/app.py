from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import pdfkit
import os
import tempfile
import random
import string
from flask_mail import Mail, Message
import hashlib
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-in-production'  # Change this in production

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': '',
    'password': '',
    'database': 'vendor_registration'
}

# Email Configuration (Update with your email settings)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ''  # Replace with your email
app.config['MAIL_PASSWORD'] = ''     # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = ''

mail = Mail(app)

# Configure pdfkit - UPDATE THIS PATH TO YOUR WKHTMLTOPDF LOCATION
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'no-outline': None
}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('signup_page'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Create database connection"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_tables():
    """Create all necessary tables"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Create users table for authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create OTP table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_verification (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                otp VARCHAR(6) NOT NULL,
                purpose VARCHAR(50) DEFAULT 'signup',
                expires_at DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_expires (expires_at)
            )
        """)
        
        # Create registrations table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                registration_number VARCHAR(50),
                domain_type VARCHAR(50),
                vendor_name VARCHAR(255),
                website VARCHAR(255),
                industry_type VARCHAR(100),
                contact_no VARCHAR(50),
                cin_no VARCHAR(100),
                tan_no VARCHAR(100),
                gst VARCHAR(100),
                gst_certificate VARCHAR(10),
                pan VARCHAR(100),
                pan_certificate VARCHAR(10),
                billing_address_type VARCHAR(100),
                billing_line1 TEXT,
                billing_line2 TEXT,
                billing_line3 TEXT,
                billing_city VARCHAR(100),
                billing_state VARCHAR(100),
                billing_pin VARCHAR(50),
                shipping_address_type VARCHAR(100),
                shipping_line1 TEXT,
                shipping_line2 TEXT,
                shipping_line3 TEXT,
                shipping_city VARCHAR(100),
                shipping_state VARCHAR(100),
                shipping_pin VARCHAR(50),
                bank_name VARCHAR(255),
                branch_name VARCHAR(255),
                account_no VARCHAR(100),
                account_type VARCHAR(100),
                ifsc VARCHAR(50),
                micr VARCHAR(50),
                it_contact_name VARCHAR(255),
                it_designation VARCHAR(255),
                it_email VARCHAR(255),
                it_mobile VARCHAR(50),
                it_landline VARCHAR(50),
                purchase_contact_name VARCHAR(255),
                purchase_designation VARCHAR(255),
                purchase_email VARCHAR(255),
                purchase_mobile VARCHAR(50),
                purchase_landline VARCHAR(50),
                accounts_contact_name VARCHAR(255),
                accounts_designation VARCHAR(255),
                accounts_email VARCHAR(255),
                accounts_mobile VARCHAR(50),
                accounts_landline VARCHAR(50),
                finance_contact_name VARCHAR(255),
                finance_designation VARCHAR(255),
                finance_email VARCHAR(255),
                finance_mobile VARCHAR(50),
                finance_landline VARCHAR(50),
                declarant_name VARCHAR(255),
                declarant_designation VARCHAR(255),
                declarant_date DATE,
                declarant_signature VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Tables created successfully")

# OTP Generation Functions
def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def send_otp_email(email, otp, purpose="signup"):
    """Send OTP via email"""
    try:
        if purpose == "signup":
            subject = "ITCG - Verify Your Email for Registration"
            message = "Thank you for signing up! Please verify your email address."
        elif purpose == "login":
            subject = "ITCG - Login Verification OTP"
            message = "You requested to login to your account."
        else:
            subject = "ITCG - OTP Verification"
            message = "Your OTP for verification is below."
            
        msg = Message(
            subject=subject,
            recipients=[email]
        )
        msg.body = f"""
        Dear User,
        
        {message}
        
        Your OTP is: {otp}
        
        This OTP is valid for 10 minutes.
        
        If you did not request this, please ignore this email.
        
        Regards,
        ITCG Team
        """
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #333; border-bottom: 2px solid #333; padding-bottom: 10px;">ITCG Registration Portal</h2>
            <p style="font-size: 16px;">Dear User,</p>
            <p style="font-size: 16px;">{message}</p>
            <div style="background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; border-radius: 5px; margin: 20px 0;">
                {otp}
            </div>
            <p style="font-size: 14px; color: #666;">This OTP is valid for <strong>10 minutes</strong>.</p>
            <p style="font-size: 14px; color: #666;">If you did not request this, please ignore this email.</p>
            <hr style="border: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 12px; color: #999;">Regards,<br>ITCG Team</p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def save_otp(email, otp, purpose="signup", expiry_minutes=10):
    """Save OTP to database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(minutes=expiry_minutes)
    
    # Delete old OTPs for this email
    cursor.execute("DELETE FROM otp_verification WHERE email = %s", (email,))
    
    # Insert new OTP
    cursor.execute(
        "INSERT INTO otp_verification (email, otp, purpose, expires_at) VALUES (%s, %s, %s, %s)",
        (email, otp, purpose, expires_at)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    return True

def verify_otp(email, otp, purpose="signup"):
    """Verify OTP"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM otp_verification WHERE email = %s AND otp = %s AND purpose = %s AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1",
        (email, otp, purpose)
    )
    result = cursor.fetchone()
    
    if result:
        # Delete used OTP
        cursor.execute("DELETE FROM otp_verification WHERE id = %s", (result['id'],))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    cursor.close()
    conn.close()
    return False

# ==================== ROUTES ====================

# HOME ROUTE - Redirects to signup page (First Page)
@app.route('/')
def home():
    """Home page redirects to signup"""
    if 'user_id' in session:
        return redirect(url_for('registration_page'))
    return redirect(url_for('signup_page'))

# SIGNUP PAGE (First Page)
@app.route('/signup')
def signup_page():
    """Render signup page (first page)"""
    if 'user_id' in session:
        return redirect(url_for('registration_page'))
    return render_template('signup.html')

# LOGIN PAGE (Second Page)
@app.route('/login')
def login_page():
    """Render login page (after signup)"""
    if 'user_id' in session:
        return redirect(url_for('registration_page'))
    return render_template('login.html')

# REGISTRATION PAGE (Third Page - Protected)
@app.route('/registration')
@login_required
def registration_page():
    """Render registration form page (after login)"""
    return render_template('index.html', user_name=session.get('user_name'))

# ==================== API ROUTES ====================

# SIGNUP APIs
@app.route('/api/signup/send-otp', methods=['POST'])
def signup_send_otp():
    """Send OTP for signup"""
    data = request.json
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    
    if not email or not password or not name:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    # Check if user already exists
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if existing_user:
        return jsonify({'success': False, 'error': 'Email already registered. Please login.'}), 400
    
    # Store signup data in session temporarily
    session['signup_email'] = email
    session['signup_name'] = name
    session['signup_password'] = hash_password(password)
    
    # Generate and send OTP
    otp = generate_otp()
    if save_otp(email, otp, 'signup'):
        if send_otp_email(email, otp, 'signup'):
            return jsonify({'success': True, 'message': 'OTP sent successfully'})
    
    return jsonify({'success': False, 'error': 'Failed to send OTP'}), 500

@app.route('/api/signup/verify-otp', methods=['POST'])
def signup_verify_otp():
    """Verify OTP and create account"""
    data = request.json
    otp = data.get('otp')
    
    email = session.get('signup_email')
    name = session.get('signup_name')
    password = session.get('signup_password')
    
    if not email or not name or not password:
        return jsonify({'success': False, 'error': 'Session expired. Please start over.'}), 400
    
    if verify_otp(email, otp, 'signup'):
        # Create user account
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (email, password, name, is_verified) VALUES (%s, %s, %s, %s)",
                (email, password, name, True)
            )
            conn.commit()
            
            # Clear signup session data
            session.pop('signup_email', None)
            session.pop('signup_name', None)
            session.pop('signup_password', None)
            
            # Store success message in session
            session['signup_success'] = True
            session['signup_email'] = email
            
            return jsonify({'success': True, 'message': 'Account created successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    
    return jsonify({'success': False, 'error': 'Invalid or expired OTP'}), 400

# LOGIN APIs
@app.route('/api/login/send-otp', methods=['POST'])
def login_send_otp():
    """Send OTP for login"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400
    
    # Check if user exists
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'error': 'Email not registered. Please sign up first.'}), 404
    
    # Store email in session
    session['login_email'] = email
    
    # Generate and send OTP
    otp = generate_otp()
    if save_otp(email, otp, 'login'):
        if send_otp_email(email, otp, 'login'):
            return jsonify({'success': True, 'message': 'OTP sent successfully'})
    
    return jsonify({'success': False, 'error': 'Failed to send OTP'}), 500

@app.route('/api/login/verify-otp', methods=['POST'])
def login_verify_otp():
    """Verify OTP and login"""
    data = request.json
    otp = data.get('otp')
    
    email = session.get('login_email')
    
    if not email:
        return jsonify({'success': False, 'error': 'Session expired. Please start over.'}), 400
    
    if verify_otp(email, otp, 'login'):
        # Get user details
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            
            # Clear login session data
            session.pop('login_email', None)
            
            return jsonify({'success': True, 'message': 'Login successful'})
    
    return jsonify({'success': False, 'error': 'Invalid or expired OTP'}), 400

# LOGOUT
@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# REGISTRATION FORM SUBMIT
@app.route('/submit', methods=['POST'])
@login_required
def submit_form():
    try:
        data = request.json
        conn = get_db_connection()
        
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        query = """
        INSERT INTO registrations (
            user_id, registration_number, domain_type, vendor_name, website, industry_type, contact_no,
            cin_no, tan_no, gst, gst_certificate, pan, pan_certificate,
            billing_address_type, billing_line1, billing_line2, billing_line3,
            billing_city, billing_state, billing_pin,
            shipping_address_type, shipping_line1, shipping_line2, shipping_line3,
            shipping_city, shipping_state, shipping_pin,
            bank_name, branch_name, account_no, account_type, ifsc, micr,
            it_contact_name, it_designation, it_email, it_mobile, it_landline,
            purchase_contact_name, purchase_designation, purchase_email, purchase_mobile, purchase_landline,
            accounts_contact_name, accounts_designation, accounts_email, accounts_mobile, accounts_landline,
            finance_contact_name, finance_designation, finance_email, finance_mobile, finance_landline,
            declarant_name, declarant_designation, declarant_date, declarant_signature
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        """
        
        values = (
            session['user_id'], data.get('registrationNumber'), data.get('domainType'), 
            data.get('vendorName'), data.get('website'), data.get('industry'), 
            data.get('contactNo'), data.get('cin'), data.get('tan'), 
            data.get('gst'), data.get('gstCert'), data.get('pan'), data.get('panCert'),
            data.get('billType'), data.get('billLine1'), data.get('billLine2'),
            data.get('billLine3'), data.get('billCity'), data.get('billState'),
            data.get('billPin'), data.get('shipType'), data.get('shipLine1'),
            data.get('shipLine2'), data.get('shipLine3'), data.get('shipCity'),
            data.get('shipState'), data.get('shipPin'),
            data.get('bankName'), data.get('branchName'), data.get('accountNo'),
            data.get('accountType'), data.get('ifsc'), data.get('micr'),
            data.get('itName'), data.get('itDesig'), data.get('itEmail'),
            data.get('itMobile'), data.get('itLandline'),
            data.get('purName'), data.get('purDesig'), data.get('purEmail'),
            data.get('purMobile'), data.get('purLandline'),
            data.get('accName'), data.get('accDesig'), data.get('accEmail'),
            data.get('accMobile'), data.get('accLandline'),
            data.get('finName'), data.get('finDesig'), data.get('finEmail'),
            data.get('finMobile'), data.get('finLandline'),
            data.get('declName'), data.get('declDesig'), data.get('declDate'),
            data.get('signature')
        )
        
        cursor.execute(query, values)
        conn.commit()
        registration_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Data saved successfully',
            'id': registration_id,
            'registrationNumber': data.get('registrationNumber'),
            'previewUrl': f'/preview/{registration_id}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# UPLOAD DOCUMENTS ROUTE — saves GST/PAN files to their own folders
@app.route('/upload-documents', methods=['POST'])
@login_required
def upload_documents():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        gst_folder = os.path.join(BASE_DIR, 'uploads', 'GST')
        pan_folder = os.path.join(BASE_DIR, 'uploads', 'PAN')
        os.makedirs(gst_folder, exist_ok=True)
        os.makedirs(pan_folder, exist_ok=True)

        gst_number = request.form.get('gst_number', '').strip()
        pan_number = request.form.get('pan_number', '').strip()

        saved = []

        # Save GST file — named after GST number, keep original extension
        gst_file = request.files.get('gstFile')
        if gst_file and gst_file.filename and gst_number:
            ext = os.path.splitext(gst_file.filename)[1].lower() or '.pdf'
            filename = gst_number + ext
            gst_file.save(os.path.join(gst_folder, filename))
            saved.append('GST')

        # Save PAN file — named after PAN number, keep original extension
        pan_file = request.files.get('panFile')
        if pan_file and pan_file.filename and pan_number:
            ext = os.path.splitext(pan_file.filename)[1].lower() or '.pdf'
            filename = pan_number + ext
            pan_file.save(os.path.join(pan_folder, filename))
            saved.append('PAN')

        return jsonify({'success': True, 'saved': saved})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# PREVIEW ROUTE (new - before PDF download)
@app.route('/preview/<int:registration_id>', methods=['GET'])
@login_required
def preview_registration(registration_id):
    try:
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('registration_page'))
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM registrations WHERE id = %s AND user_id = %s",
                      (registration_id, session['user_id']))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if not data:
            return redirect(url_for('registration_page'))
        if data.get('declarant_date') and hasattr(data['declarant_date'], 'strftime'):
            data['declarant_date'] = data['declarant_date'].strftime('%d-%m-%Y')
        return render_template('preview.html', data=data, user_name=session.get('user_name'))
    except Exception as e:
        return redirect(url_for('registration_page'))

# EDIT FORM ROUTE
@app.route('/edit-form/<int:registration_id>', methods=['GET'])
@login_required
def edit_form(registration_id):
    try:
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('registration_page'))
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM registrations WHERE id = %s AND user_id = %s",
                      (registration_id, session['user_id']))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if not data:
            return redirect(url_for('registration_page'))
        if data.get('declarant_date') and hasattr(data['declarant_date'], 'strftime'):
            data['declarant_date'] = data['declarant_date'].strftime('%Y-%m-%d')
        return render_template('edit_form.html', data=data, user_name=session.get('user_name'))
    except Exception as e:
        return redirect(url_for('registration_page'))

# UPDATE REGISTRATION
@app.route('/update/<int:registration_id>', methods=['POST'])
@login_required
def update_registration(registration_id):
    try:
        data = request.json
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        cursor = conn.cursor()
        query = """
        UPDATE registrations SET
            domain_type=%s, vendor_name=%s, website=%s, industry_type=%s, contact_no=%s,
            cin_no=%s, tan_no=%s, gst=%s, gst_certificate=%s, pan=%s, pan_certificate=%s,
            billing_address_type=%s, billing_line1=%s, billing_line2=%s, billing_line3=%s,
            billing_city=%s, billing_state=%s, billing_pin=%s,
            shipping_address_type=%s, shipping_line1=%s, shipping_line2=%s, shipping_line3=%s,
            shipping_city=%s, shipping_state=%s, shipping_pin=%s,
            bank_name=%s, branch_name=%s, account_no=%s, account_type=%s, ifsc=%s, micr=%s,
            it_contact_name=%s, it_designation=%s, it_email=%s, it_mobile=%s, it_landline=%s,
            purchase_contact_name=%s, purchase_designation=%s, purchase_email=%s, purchase_mobile=%s, purchase_landline=%s,
            accounts_contact_name=%s, accounts_designation=%s, accounts_email=%s, accounts_mobile=%s, accounts_landline=%s,
            finance_contact_name=%s, finance_designation=%s, finance_email=%s, finance_mobile=%s, finance_landline=%s,
            declarant_name=%s, declarant_designation=%s, declarant_date=%s, declarant_signature=%s
        WHERE id=%s AND user_id=%s
        """
        values = (
            data.get('domainType'), data.get('vendorName'), data.get('website'),
            data.get('industry'), data.get('contactNo'),
            data.get('cin'), data.get('tan'), data.get('gst'), data.get('gstCert'),
            data.get('pan'), data.get('panCert'),
            data.get('billType'), data.get('billLine1'), data.get('billLine2'), data.get('billLine3'),
            data.get('billCity'), data.get('billState'), data.get('billPin'),
            data.get('shipType'), data.get('shipLine1'), data.get('shipLine2'), data.get('shipLine3'),
            data.get('shipCity'), data.get('shipState'), data.get('shipPin'),
            data.get('bankName'), data.get('branchName'), data.get('accountNo'),
            data.get('accountType'), data.get('ifsc'), data.get('micr'),
            data.get('itName'), data.get('itDesig'), data.get('itEmail'), data.get('itMobile'), data.get('itLandline'),
            data.get('purName'), data.get('purDesig'), data.get('purEmail'), data.get('purMobile'), data.get('purLandline'),
            data.get('accName'), data.get('accDesig'), data.get('accEmail'), data.get('accMobile'), data.get('accLandline'),
            data.get('finName'), data.get('finDesig'), data.get('finEmail'), data.get('finMobile'), data.get('finLandline'),
            data.get('declName'), data.get('declDesig'), data.get('declDate'), data.get('signature'),
            registration_id, session['user_id']
        )
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# GENERATE PDF
@app.route('/generate-pdf/<int:registration_id>', methods=['GET'])
@login_required
def generate_pdf(registration_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM registrations WHERE id = %s AND user_id = %s", 
                      (registration_id, session['user_id']))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not data:
            return jsonify({'error': 'Registration not found'}), 404
        
        if data['declarant_date']:
            data['declarant_date'] = data['declarant_date'].strftime('%d-%m-%Y')
        
        html_content = render_template('pdf_template.html', data=data)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdfkit.from_string(html_content, tmp_file.name, configuration=PDFKIT_CONFIG, options=PDF_OPTIONS)
            tmp_file_path = tmp_file.name
        
        filename = f"ITCG_Registration_{data.get('registration_number', registration_id)}.pdf"
        
        return send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5000)
