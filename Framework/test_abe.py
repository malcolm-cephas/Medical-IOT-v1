
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/abe"

def run_test():
    print("=== Testing ABE APIs ===")

    # 1. Setup
    print("\n[1] Testing Setup...")
    try:
        resp = requests.post(f"{BASE_URL}/setup")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Setup failed: {e}")
        return

    # 2. KeyGen (Success Case)
    print("\n[2] Testing KeyGen for 'doctor'...")
    user_key = None
    try:
        payload = {
            "username": "dr_strange",
            "attributes": ["doctor", "cardiology", "staff"]
        }
        resp = requests.post(f"{BASE_URL}/keygen", json=payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            user_key = resp.json().get("user_key")
            print("Received User Key.")
        else:
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"KeyGen failed: {e}")
        return

    if not user_key:
        print("Stopping test due to KeyGen failure.")
        return

    # 3. Encrypt
    print("\n[3] Testing Encrypt with policy 'doctor' AND 'cardiology'...")
    ciphertext_package = None
    try:
        payload = {
            "message": "Patient has severe arrhythmia.",
            "policy": ["doctor", "cardiology"]
        }
        resp = requests.post(f"{BASE_URL}/encrypt", json=payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            ciphertext_package = resp.json().get("ciphertext")
            print("Received Ciphertext.")
        else:
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Encrypt failed: {e}")
        return

    if not ciphertext_package:
        print("Stopping test due to Encrypt failure.")
        return

    # 4. Decrypt (Success Case)
    print("\n[4] Testing Decrypt (Authorized)...")
    try:
        payload = {
            "ciphertext": ciphertext_package,
            "user_key": user_key
        }
        resp = requests.post(f"{BASE_URL}/decrypt", json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        if resp.status_code == 200:
            print("Decryption SUCCESS!")
        else:
            print("Decryption FAILED!")
    except Exception as e:
        print(f"Decrypt failed: {e}")

    # 5. Decrypt (Failure Case - Insufficient Attributes)
    print("\n[5] Testing Decrypt (Unauthorized - Nurse Key)...")
    nurse_key = None
    try:
        # Generate Nurse Key
        resp = requests.post(f"{BASE_URL}/keygen", json={"username": "nurse_joy", "attributes": ["nurse", "staff"]})
        if resp.status_code == 200:
            nurse_key = resp.json().get("user_key")
        
        if nurse_key:
            payload = {
                "ciphertext": ciphertext_package,
                "user_key": nurse_key
            }
            resp = requests.post(f"{BASE_URL}/decrypt", json=payload)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.json()}")
            if resp.status_code != 200:
                print("Decryption correctly BLOCKED.")
            else:
                print("ERROR: Decryption should have failed!")
    except Exception as e:
        print(f"Unauthorized Decrypt test failed: {e}")

if __name__ == "__main__":
    # Ensure server is running before running this test
    # You might need to start the flask app in a separate terminal: python run.py
    run_test()
