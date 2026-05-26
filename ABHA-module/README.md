# ABHA Biometric Database & Verification Module

This module provides a simulator and developer interface for integrating local biometric identities (128-dimensional face encoding vectors) with the national Ayushman Bharat Health Account (ABHA) database.

Using SQLite, it registers a custom Python-driven Euclidean distance calculation, enabling extremely fast, database-level similarity search for biometric vector matching.

---

## Getting Started

### 1. Prerequisites
Ensure you have **Python 3.12** installed on your system.

### 2. Setup the Virtual Environment
Navigate to the project root directory and run:

```powershell
# Create the virtual environment
py -3.12 -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Quickstart Guide

Here is how you can use the module in your Python codebase:

### 1. Initialize and Seed the Databases
Before querying, you must initialize the databases (`abha.db` and `raya.db`) and seed them with simulated patient and biometric profiles:

```python
from database import clear_abha_db, clear_raya_db, seed_abha_db, init_raya_db

# Reset and seed databases
clear_abha_db()
clear_raya_db()
seed_abha_db()  # Seeds patient records in abha.db
init_raya_db()  # Prepares biometric tables in raya.db
```

### 2. Register User Biometrics
You can save a user's face encoding (128-dimensional unit vector) and link it to their ABHA number:

```python
from abha_interface import BiometricMatcher

matcher = BiometricMatcher(threshold=0.6)

# Generate a mock face vector for demonstrations
new_face_vector = matcher.generate_random_encoding()

# Save the biometric profile and link to ABHA number
user_id = matcher.register_user_biometrics(
    full_name="Karan Johar",
    face_encoding=new_face_vector,
    abha_number="91-1234-5678-9012"
)
print(f"Registered user with ID: {user_id}")
```

### 3. Verify a User Biometrically
When a user stands in front of a camera scanner, capture their face encoding (simulated here by adding slight noise to the stored vector) and identify them:

```python
# Simulate repeated capture with minor noise (4% variation)
probe_vector = BiometricMatcher.generate_probe_encoding(new_face_vector, noise_level=0.04)

# Look up closest profile in the database
matched_user, distance = matcher.identify_user(probe_vector)

if matched_user:
    print(f"Biometric Match Found! Identified as: {matched_user['full_name']}")
    print(f"Euclidean Distance: {distance:.4f} (Threshold: {matcher.threshold})")
    print(f"Linked ABHA ID: {matched_user['abha_number']}")
else:
    print(f"Access Denied. Face unrecognized. Closest distance was {distance:.4f}")
```

### 4. Fetch ABHA Patient Profiles and Clinical Records
Once you obtain the user's ABHA number from their biometric profile, query their health history via the ABHA client:

```python
from abha_interface import ABHAClient

client = ABHAClient()

# Get patient's basic demographic profile
profile = client.get_patient_profile(matched_user["abha_number"])
print(f"Patient Name: {profile['full_name']}")
print(f"Mobile: {profile['mobile_number']}")

# Fetch medical health records with simulated consent ID
health_records = client.verify_consent_and_fetch_records(
    abha_number=matched_user["abha_number"],
    consent_id="CONSENT_TOKEN_101"
)

for record in health_records:
    print(f"Facility: {record['facility']} | Diagnosis: {record['diagnosis']}")
```

---

## Verifying the Project

### Running the Simulator CLI
To run the automated, color-coded demonstration showcasing identification, rejection, registration, and dynamic linkage scenarios, run:

```powershell
python main.py
```

### Running the Test Suite
The project includes a robust test suite covering vector math, SQLite operations, matching thresholds, and ABHA client features:

```powershell
python -m unittest discover -s tests
```
