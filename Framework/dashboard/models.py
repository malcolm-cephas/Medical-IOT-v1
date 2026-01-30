from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False) # doctor, nurse, patient, lab_assistant
    
    # New Profile Fields
    full_name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    department = db.Column(db.String(50), nullable=True) # For doctors: Pediatrics, Cardiology, etc.
    
    # For patients, link to a specific device/bed ID if needed, 
    # or use username as the patient_id for simplicity
    patient_device_id = db.Column(db.String(50), nullable=True) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), nullable=False) # Links to User.username or device_id
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    hr = db.Column(db.Integer)
    spo2 = db.Column(db.Integer)
    temp = db.Column(db.Float)
    hum = db.Column(db.Float)
    ecg_data = db.Column(db.Integer) # Storing single point for simplicity, or JSON for chunks
