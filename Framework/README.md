# MediSecure IoT Health Framework

A decentralized, role-based health monitoring system connecting Arduino sensors to a secure web dashboard.

## Features
- **Real-time Monitoring**: Live ECG, Heart Rate, SpO2, Temperature, and Humidity.
- **Role-Based Access**:
    - **Doctors**: View all patients and historical data.
    - **Nurses**: Central monitoring station for active devices.
    - **Patients**: Personal dashboard for their own health data.
- **Secure Auth**: Sign-up and Login system with password hashing.
- **Database**: SQLite storage for user profiles and health records.

## Quick Start

### 1. Prerequisites
- Python 3.8+
- Arduino IDE (for hardware)

### 2. Installation
1.  Navigate to the project folder:
    ```bash
    cd "path"
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Running the Web App
1.  Start the Flask server:
    ```bash
    python dashboard/app.py
    ```
    *(Note: If you see module errors, run `$env:PYTHONPATH="."; python dashboard/app.py`)*

2.  Open your browser and go to:
    **http://localhost:5000**

### 4. Simulating Data (No Hardware)
To see the dashboard in action without sensors:
1.  Open a **new terminal**.
2.  Run the mock generator:
    ```bash
    python mock_data_generator.py
    ```
3.  Login as `doctor` / `doctor123` or `nurse` / `nurse123` to see the data coming in.

### 5. Hardware Setup (Arduino)
1.  Open `arduino_firmware/health_monitor.ino` in Arduino IDE.
2.  Install libraries: `WiFiS3`, `Arduino_LED_Matrix`, `DHT sensor library`, `SparkFun MAX3010x`.
3.  Update WiFi credentials and your PC's IP address in the code.
4.  Upload to Arduino Uno R4 WiFi.

## Default Credentials
| Role | Username | Password |
|------|----------|----------|
| **Doctor** | `doctor` | `doctor123` |
| **Nurse** | `nurse` | `nurse123` |
| **Patient** | `patient_alpha` | `patient123` |

## Project Structure
- `dashboard/`: Python Flask Web App
- `arduino_firmware/`: C++ Code for Arduino Uno R4
- `mock_data_generator.py`: Simulation script
- `requirements.txt`: Python dependencies
