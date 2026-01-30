# MediSecure Web App Walkthrough

I have successfully upgraded the system to a **Full Web Application** with a database, role-based access control, **User Registration**, a **Standalone Executable**, and a **Premium Dark/Light Mode UI**.

## Features
1.  **Authentication**: Secure login system with role-based redirection.
2.  **Sign Up**: New users can create accounts with specific roles (Doctor, Nurse, Patient, etc.).
3.  **Database**: SQLite database (`health.db`) stores user accounts and health records.
4.  **Role-Based Dashboards**:
    - **Doctor**: View all patients and system stats.
    - **Nurse**: Real-time monitoring station for active devices.
    - **Patient**: Personal dashboard showing only their own data.
5.  **Standalone App**: Run the system without installing Python.
6.  **Theme Toggle**: Switch between Dark and Light modes with a premium look.
7.  **Mock Data Generator**: Standalone tool to simulate patient data.
8.  **Stop Script**: Quickly terminate all running processes.
9.  **Arduino Integration**: Firmware ready for ESP32/Arduino R4 WiFi.

## How to Access

### 1. Run the Main Application
-   **Option A (Executable)**: Go to `dist/MediSecure/` and run **`MediSecure.exe`**.
-   **Option B (Source)**: Run `python run.py`.
-   Access at: `http://localhost:5000` or `http://10.159.251.149:5000`

### 2. Run the Mock Data Generator
To simulate patient data (ECG, Heart Rate, etc.):
-   **Option A (Executable)**: Go to `dist/` and run **`MockDataGenerator.exe`**.
-   **Option B (Batch File)**: Double-click **`run_mock_data.bat`** in the project root.
-   **Option C (Source)**: Run `python mock_data_generator.py`.
-   **Note**: This is now configured to send data to `http://10.159.251.149:5000`.

### 3. Stop All Processes
To close everything (Server, Data Generator, Python):
-   Double-click **`stop_all.bat`** in the project root.

### 4. Configure Arduino
The firmware is located at: `arduino_firmware/health_monitor/health_monitor.ino`
**Configuration Updated**:
-   **Server IP**: `10.159.251.149`
-   **Arduino Static IP**: `10.159.251.52`
-   **Gateway**: `10.159.251.1` (Default assumption, change if needed)

## Creating an Account
1.  Go to `http://localhost:5000/login`.
2.  Click **"Create Account"**.
3.  Fill in your details (Name, Age, Role).
4.  Submit and Login.

## Verification
I have verified the system by:
1.  Running the `MediSecure.exe` file.
2.  Logging in as a Doctor.
3.  Verifying the dashboard loads without errors.
4.  Testing the Theme Toggle and verifying the polished Light Mode.
5.  **Fixed**: Input text is now clearly visible in Light Mode.
6.  **Fixed**: Theme toggle is present and functional.
7.  **Polished**: Buttons and links have premium styling.
8.  **New**: `MockDataGenerator.exe` successfully sends simulated data.
9.  **New**: `stop_all.bat` successfully kills all related processes.
10. **New**: Arduino firmware integrated with correct JSON keys and Static IP.

![Premium UI Verified](/premium_ui_verified_1764389965455.png)
