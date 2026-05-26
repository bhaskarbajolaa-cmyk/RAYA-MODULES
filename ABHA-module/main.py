import os
import sys
import json
from typing import Dict, Any, List

# Add workspace root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    clear_abha_db,
    clear_raya_db,
    seed_abha_db,
    init_raya_db,
    get_all_raya_users,
    update_user_abha_link,
    delete_inactive_users
)
from abha_interface import ABHAClient, BiometricMatcher

# ANSI terminal colors for styling the output
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
BLUE = "\033[34m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
PURPLE = "\033[35m"

def print_header(title: str):
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN} {title.center(58)} {RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}")

def print_success(message: str):
    print(f"{GREEN}[SUCCESS] {message}{RESET}")

def print_warning(message: str):
    print(f"{YELLOW}[WARNING] {message}{RESET}")

def print_error(message: str):
    print(f"{RED}[ERROR] {message}{RESET}")

def print_info(message: str):
    print(f"{BLUE}[INFO] {message}{RESET}")

def main():
    print_header("ABHA Biometric Embedding DB Simulator")
    
    # 1. Initialize and seed databases
    print_info("Initializing and seeding Databases...")
    clear_abha_db()
    clear_raya_db()
    
    # Seed ABHA Central Database
    seed_abha_db()
    print_success("Seeded ABHA database with 5 patient health profiles.")
    
    # Seed RAYA Database with Biometric Encodings
    init_raya_db()
    
    # Instantiate modules
    abha_client = ABHAClient()
    matcher = BiometricMatcher(threshold=0.6)
    
    # We will seed the RAYA database with users corresponding to ABHA profiles
    # generate a stable random 128-D vector for each seeded patient
    abha_users = [
        {"name": "Suresh Kumar", "abha": "91-1111-2222-3333"},
        {"name": "Priya Sharma", "abha": "91-4444-5555-6666"},
        {"name": "Amit Patel", "abha": "91-7777-8888-9999"},
        {"name": "Ananya Sen", "abha": "91-1234-5678-9012"},
        {"name": "Rahul Verma", "abha": "91-9876-5432-1098"}
    ]
    
    stored_profiles = {} # To keep track of user name -> face encoding mapping in Python
    
    for u in abha_users:
        vector = matcher.generate_random_encoding()
        user_id = matcher.register_user_biometrics(u["name"], vector, u["abha"])
        stored_profiles[u["name"]] = {
            "id": user_id,
            "name": u["name"],
            "vector": vector,
            "abha": u["abha"]
        }
        
    # Also insert a user who is registered locally in RAYA but NOT linked to ABHA
    local_only_name = "John Doe"
    jd_vector = matcher.generate_random_encoding()
    jd_id = matcher.register_user_biometrics(local_only_name, jd_vector, abha_number=None)
    stored_profiles[local_only_name] = {
        "id": jd_id,
        "name": local_only_name,
        "vector": jd_vector,
        "abha": None
    }
    
    print_success(f"Seeded RAYA local biometric database with 6 users (5 linked, 1 unlinked).")
    
    # 2. RUN SIMULATION SCENARIOS
    
    # --- SCENARIO A: Successful biometric identification and ABHA profile lookup ---
    print_header("SCENARIO A: Biometric Login - Priya Sharma")
    print_info("Simulating repeated biometric capture for Priya Sharma...")
    
    priya_base_vec = stored_profiles["Priya Sharma"]["vector"]
    # Simulating a capture by adding noise (sigma = 0.04)
    priya_probe = matcher.generate_probe_encoding(priya_base_vec, noise_level=0.04)
    
    print(f"Base Vector sample (first 5 floats):  {[round(x, 4) for x in priya_base_vec[:5]]}")
    print(f"Probe Vector sample (first 5 floats): {[round(x, 4) for x in priya_probe[:5]]}")
    
    user_match, distance = matcher.identify_user(priya_probe)
    
    if user_match:
        print_success(f"Biometric Match Found!")
        print(f"  {BOLD}Identified User:{RESET} {user_match['full_name']}")
        print(f"  {BOLD}Euclidean Distance:{RESET} {distance:.4f} (Threshold: {matcher.threshold})")
        
        abha_num = user_match["abha_number"]
        print_info(f"Retrieving linked ABHA Profile for Health ID: {abha_num}...")
        
        profile = abha_client.get_patient_profile(abha_num)
        if profile:
            print(f"  {BOLD}Full Name:{RESET}      {profile['full_name']}")
            print(f"  {BOLD}DOB/Gender:{RESET}     {profile['date_of_birth']} / {profile['gender']}")
            print(f"  {BOLD}ABHA Address:{RESET}   {profile['abha_address']}")
            print(f"  {BOLD}Mobile Number:{RESET}  {profile['mobile_number']}")
            
            records = abha_client.verify_consent_and_fetch_records(abha_num, consent_id="CONSENT_1234")
            print(f"  {BOLD}Clinical Records:{RESET}")
            if records:
                for idx, record in enumerate(records, 1):
                    print(f"    {BOLD}Record #{idx}:{RESET} Date: {record['date']} | Facility: {record['facility']} | Doctor: {record['doctor']}")
                    print(f"               Diagnosis: {record['diagnosis']}")
                    if "prescription" in record:
                        print(f"               Prescription: {record['prescription']}")
                    if "notes" in record:
                        print(f"               Notes: {record['notes']}")
            else:
                print_warning("No clinical health records found for this patient.")
        else:
            print_error("Failed to fetch ABHA profile. Number might be deactivated or invalid.")
    else:
        print_error(f"Access Denied. Face unrecognized. Closest distance was {distance:.4f}.")

    # --- SCENARIO B: Unregistered person tries to log in ---
    print_header("SCENARIO B: Biometric Access - Unknown Visitor")
    print_info("Simulating biometric scan of an unregistered user...")
    unknown_probe = matcher.generate_random_encoding()
    
    user_match, distance = matcher.identify_user(unknown_probe)
    
    if user_match:
        print_success(f"Biometric Match Found! Identified as {user_match['full_name']}.")
    else:
        print_error("Access Denied. Face unrecognized.")
        print(f"  {BOLD}Best Match Distance:{RESET} {distance:.4f} (Threshold: {matcher.threshold})")
        print_info("As Euclidean distance exceeds the threshold, this individual is rejected.")

    # --- SCENARIO C: Local user exists but is not linked to ABHA ---
    print_header("SCENARIO C: Unlinked User - John Doe")
    print_info("Simulating biometric scan for John Doe...")
    
    jd_base_vec = stored_profiles["John Doe"]["vector"]
    jd_probe = matcher.generate_probe_encoding(jd_base_vec, noise_level=0.03)
    
    user_match, distance = matcher.identify_user(jd_probe)
    
    if user_match:
        print_success("Biometric Match Found!")
        print(f"  {BOLD}Identified User:{RESET} {user_match['full_name']}")
        print(f"  {BOLD}Euclidean Distance:{RESET} {distance:.4f}")
        
        abha_num = user_match["abha_number"]
        if not abha_num:
            print_warning("User is registered locally in RAYA but does not have a linked ABHA number.")
            
            # Simulate Registration and Linking
            print_info("Simulating Registration & Linking Flow...")
            print("Creating new ABHA record for John Doe...")
            new_abha = abha_client.register_new_abha(
                full_name="John Doe",
                date_of_birth="1992-04-14",
                gender="M",
                mobile_number="9877889900",
                preferred_address_prefix="john_doe"
            )
            print_success(f"Generated new central ABHA Number: {new_abha['abha_number']}")
            print(f"  ABHA Address assigned: {new_abha['abha_address']}")
            
            print_info("Linking new ABHA number to local RAYA profile...")
            update_user_abha_link(user_match["id"], new_abha["abha_number"])
            print_success("Link updated successfully in local SQLite database!")
            
            # Verify the link now works
            print_info("Re-scanning John Doe's biometrics to verify ABHA linkage...")
            updated_user, new_dist = matcher.identify_user(jd_probe)
            if updated_user and updated_user["abha_number"]:
                print_success(f"Verification Successful! Linked ABHA: {updated_user['abha_number']}")
                profile = abha_client.get_patient_profile(updated_user["abha_number"])
                print(f"  {BOLD}Profile Name:{RESET}      {profile['full_name']}")
                print(f"  {BOLD}ABHA Address:{RESET}   {profile['abha_address']}")
                print(f"  {BOLD}Health Records:{RESET} {profile['health_records']} (None yet; freshly registered)")
            else:
                print_error("Failed to verify updated linkage.")
        else:
            print_success(f"Linked ABHA number found: {abha_num}")
    else:
        print_error("User not found.")

    # --- SCENARIO D: Auto-cleanup of inactive profiles ---
    print_header("SCENARIO D: Biometric Stale Profile Auto-Cleanup")
    print_info("Registering 'Stale Steve' in the local system...")
    steve_vec = matcher.generate_random_encoding()
    steve_id = matcher.register_user_biometrics("Stale Steve", steve_vec, abha_number=None)
    print_success(f"Registered Stale Steve (User ID: {steve_id}).")
    
    # Manually backdating Steve's check-in to 45 days ago in the SQLite database
    import sqlite3
    from database import RAYA_DB_PATH
    print_info("Simulating passing of time: Backdating Steve's check-in to 45 days ago...")
    conn = sqlite3.connect(RAYA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE raya_users SET last_checkin = datetime('now', '-45 days') WHERE id = ?", (steve_id,))
    conn.commit()
    conn.close()
    print_success("Backdated Stale Steve's check-in in the database successfully.")
    
    # Check total user count
    users_before = len(get_all_raya_users())
    print(f"Total profiles in local database before cleanup: {users_before}")
    
    # Run cleanup for profiles inactive for more than 30 days
    print_info("Running database cleanup for profiles inactive for > 30 days...")
    deleted = delete_inactive_users(inactive_days=30)
    print_success(f"Cleanup finished! Removed {deleted} stale profile(s).")
    
    # Check total user count again
    users_after = len(get_all_raya_users())
    print(f"Total profiles in local database after cleanup: {users_after}")
    
    # Confirm Steve is deleted
    remaining_names = [u["full_name"] for u in get_all_raya_users()]
    if "Stale Steve" not in remaining_names:
        print_success("Confirmed: Stale Steve's biometric record was permanently deleted.")
    else:
        print_error("Failed: Stale Steve's profile was not deleted.")

    print_header("Simulation Finished")

if __name__ == "__main__":
    main()
