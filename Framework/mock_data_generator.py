import requests
import time
import random
import math
import threading

SERVER_URL = "http://127.0.0.1:5000/data"

def generate_ecg_point(t):
    """Simulates a basic ECG waveform"""
    p_wave = 0.1 * math.exp(-((t % 1.0) - 0.2)**2 / 0.005)
    q_wave = -0.15 * math.exp(-((t % 1.0) - 0.35)**2 / 0.002)
    r_wave = 1.0 * math.exp(-((t % 1.0) - 0.4)**2 / 0.002)
    s_wave = -0.2 * math.exp(-((t % 1.0) - 0.45)**2 / 0.002)
    t_wave = 0.2 * math.exp(-((t % 1.0) - 0.7)**2 / 0.01)
    return (p_wave + q_wave + r_wave + s_wave + t_wave) * 500 + 512

def simulate_patient(patient_id):
    print(f"Starting simulation for {patient_id}...")
    t = random.random() # Random start time offset
    while True:
        ecg = int(generate_ecg_point(t)) + random.randint(-10, 10)
        hr = 75 + random.randint(-5, 5)
        spo2 = 98 + random.randint(-1, 1)
        temp = 36.5 + random.uniform(-0.2, 0.2)
        hum = 45 + random.uniform(-2, 2)

        payload = {
            "patient_id": patient_id,
            "ecg": ecg,
            "hr": hr,
            "spo2": spo2,
            "temp": round(temp, 1),
            "hum": round(hum, 1)
        }

        try:
            requests.post(SERVER_URL, json=payload)
        except Exception:
            pass

        t += 0.05
        time.sleep(0.1)

if __name__ == "__main__":
    # Simulate 3 patients
    patients = ["patient_alpha", "patient_beta", "patient_gamma"]
    
    threads = []
    for pid in patients:
        thread = threading.Thread(target=simulate_patient, args=(pid,))
        thread.start()
        threads.append(thread)
        
    for thread in threads:
        thread.join()
