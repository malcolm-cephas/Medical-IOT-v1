from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dashboard.models import db, User, HealthRecord
import time
import os

import sys
import os

# Determine paths for PyInstaller
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'dashboard', 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'dashboard', 'static')
    base_dir = os.path.dirname(sys.executable)
else:
    template_folder = 'templates'
    static_folder = 'static'
    base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
app.config['SECRET_KEY'] = 'secret!'

# Database path
db_path = os.path.join(base_dir, 'health.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    if current_user.role == 'doctor':
        return redirect(url_for('dashboard_doctor'))
    elif current_user.role == 'nurse':
        return redirect(url_for('dashboard_nurse'))
    elif current_user.role == 'patient':
        return redirect(url_for('dashboard_patient'))
    else:
        return "Role not recognized", 403

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
            
        new_user = User(
            username=username,
            full_name=request.form.get('full_name'),
            age=request.form.get('age'),
            role=request.form.get('role'),
            department=request.form.get('department')
        )
        new_user.set_password(request.form.get('password'))
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.')
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Role-Based Dashboards ---

@app.route('/doctor')
@login_required
def dashboard_doctor():
    if current_user.role != 'doctor': return "Access Denied", 403
    # Doctor sees all patients
    patients = User.query.filter_by(role='patient').all()
    return render_template('dashboard_doctor.html', patients=patients)

@app.route('/nurse')
@login_required
def dashboard_nurse():
    if current_user.role != 'nurse' and current_user.role != 'doctor': return "Access Denied", 403
    # Nurse sees real-time station (reusing home.html logic but passing user info)
    return render_template('dashboard_nurse.html')

@app.route('/patient')
@login_required
def dashboard_patient():
    if current_user.role != 'patient': return "Access Denied", 403
    # Patient sees only their own data
    return render_template('dashboard_patient.html', patient_id=current_user.username)

@app.route('/monitor/<patient_id>')
@login_required
def monitor_patient(patient_id):
    # Doctors and Nurses can view any patient
    if current_user.role in ['doctor', 'nurse']:
        return render_template('dashboard_patient.html', patient_id=patient_id)
    return "Access Denied", 403

# --- Data Ingestion ---

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.json
        if not data: return jsonify({"status": "error"}), 400
        
        patient_id = data.get('patient_id', 'unknown')
        
        # Save to DB
        record = HealthRecord(
            patient_id=patient_id,
            hr=data.get('hr'),
            spo2=data.get('spo2'),
            temp=data.get('temp'),
            hum=data.get('hum'),
            ecg_data=data.get('ecg')
        )
        db.session.add(record)
        db.session.commit()
        
        # Real-time emit
        socketio.emit('sensor_update', {"patient_id": patient_id, "data": data})
        
        # Update nurse station list (simplified for now, just trigger refresh)
        socketio.emit('station_update', {"patient_id": patient_id, "data": data, "last_seen": time.time()})
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ABE APIs ---
from dashboard.abe_engine import abe

@app.route('/abe/setup', methods=['POST'])
def abe_setup():
    try:
        msg = abe.setup()
        return jsonify({"status": "success", "message": msg}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/abe/keygen', methods=['POST'])
def abe_keygen():
    try:
        # Expects: {"username": "user1", "attributes": ["doctor", "cardiology"]}
        data = request.json
        username = data.get('username')
        attributes = data.get('attributes')
        
        if not username or not attributes:
            return jsonify({"status": "error", "message": "Missing username or attributes"}), 400
            
        user_key = abe.keygen(username, attributes)
        return jsonify({"status": "success", "user_key": user_key}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/abe/encrypt', methods=['POST'])
def abe_encrypt():
    try:
        # Expects: {"message": "secret data", "policy": ["doctor", "cardiology"]}
        data = request.json
        message = data.get('message')
        policy = data.get('policy')
        
        if not message or not policy:
            return jsonify({"status": "error", "message": "Missing message or policy"}), 400
            
        ciphertext_package = abe.encrypt(message, policy)
        return jsonify({"status": "success", "ciphertext": ciphertext_package}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/abe/decrypt', methods=['POST'])
def abe_decrypt():
    try:
        # Expects: {"ciphertext": {...}, "user_key": {...}}
        data = request.json
        ciphertext = data.get('ciphertext')
        user_key = data.get('user_key')
        
        if not ciphertext or not user_key:
            return jsonify({"status": "error", "message": "Missing ciphertext or user_key"}), 400
            
        decrypted_message = abe.decrypt(ciphertext, user_key)
        return jsonify({"status": "success", "message": decrypted_message}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Setup ---
def create_tables():
    with app.app_context():
        db.create_all()
        # Create default users if not exist
        if not User.query.filter_by(username='doctor').first():
            u = User(username='doctor', role='doctor')
            u.set_password('doctor123')
            db.session.add(u)
            
            u = User(username='nurse', role='nurse')
            u.set_password('nurse123')
            db.session.add(u)
            
            u = User(username='patient_alpha', role='patient')
            u.set_password('patient123')
            db.session.add(u)
            
            u = User(username='patient_beta', role='patient')
            u.set_password('patient123')
            db.session.add(u)
            
            db.session.commit()
            print("Database initialized with default users.")

if __name__ == '__main__':
    if not os.path.exists('health.db'):
        create_tables()
    print("Starting MediSecure Web App...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
