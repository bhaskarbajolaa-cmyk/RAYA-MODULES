import unittest
import numpy as np
import os
import struct
import math
from database import (
    clear_raya_db,
    init_raya_db,
    insert_raya_user,
    find_nearest_neighbor,
    serialize_vector,
    deserialize_vector,
    euclidean_distance,
    clear_abha_db,
    init_abha_db,
    seed_abha_db,
    get_patient_by_abha_number
)
from abha_interface import ABHAClient, BiometricMatcher

class TestVectorHelpers(unittest.TestCase):
    
    def test_serialization_deserialization(self):
        # Generate random 128 float list
        vec = [float(i) / 10.0 for i in range(128)]
        blob = serialize_vector(vec)
        
        # Verify length of BLOB is 512 bytes (128 * 4)
        self.assertEqual(len(blob), 512)
        
        # Deserialize and check values match
        dec_vec = deserialize_vector(blob)
        self.assertEqual(len(dec_vec), 128)
        for original, restored in zip(vec, dec_vec):
            self.assertAlmostEqual(original, restored, places=5)

    def test_invalid_vector_size(self):
        # 127 dimensions instead of 128
        invalid_vec = [1.0] * 127
        with self.assertRaises(ValueError):
            serialize_vector(invalid_vec)

    def test_euclidean_distance_math(self):
        # Setup two simple vectors
        vec1 = [0.0] * 128
        vec2 = [0.0] * 128
        
        # Match identical
        blob1 = serialize_vector(vec1)
        blob2 = serialize_vector(vec2)
        self.assertAlmostEqual(euclidean_distance(blob1, blob2), 0.0)
        
        # Match with a simple known distance
        # set index 0 of vec2 to 3.0, and index 1 to 4.0
        # Euclidean distance should be sqrt(3^2 + 4^2) = 5.0
        vec2[0] = 3.0
        vec2[1] = 4.0
        blob2_mod = serialize_vector(vec2)
        self.assertAlmostEqual(euclidean_distance(blob1, blob2_mod), 5.0)


class TestBiometricMatcher(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Set database paths to local test DBs
        # For testing, we can use the default or custom databases.
        # We will use test databases so as not to corrupt our development DBs.
        import database.connection
        import database.raya_db
        import database.abha_db
        
        cls.orig_raya_path = database.raya_db.RAYA_DB_PATH
        cls.orig_abha_path = database.abha_db.ABHA_DB_PATH
        
        database.raya_db.RAYA_DB_PATH = "test_raya.db"
        database.connection.RAYA_DB_PATH = "test_raya.db"
        database.abha_db.ABHA_DB_PATH = "test_abha.db"
        database.connection.ABHA_DB_PATH = "test_abha.db"

    @classmethod
    def tearDownClass(cls):
        # Restore original database paths
        import database.connection
        import database.raya_db
        import database.abha_db
        
        database.raya_db.RAYA_DB_PATH = cls.orig_raya_path
        database.connection.RAYA_DB_PATH = cls.orig_raya_path
        database.abha_db.ABHA_DB_PATH = cls.orig_abha_path
        database.connection.ABHA_DB_PATH = cls.orig_abha_path
        
        # Cleanup files
        for f in ["test_raya.db", "test_abha.db"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def setUp(self):
        clear_raya_db()
        init_raya_db()
        clear_abha_db()
        init_abha_db()
        self.matcher = BiometricMatcher(threshold=0.6)

    def test_nearest_neighbor_biometrics(self):
        # Generate 3 distinct base embeddings (unit vectors)
        v1 = self.matcher.generate_random_encoding()
        v2 = self.matcher.generate_random_encoding()
        
        # Make sure v1 and v2 are sufficiently distinct
        # Generate orthogonal/nearly orthogonal vectors
        # (Random high-dimensional unit vectors are very likely orthogonal, i.e., distance approx 1.41)
        
        id1 = self.matcher.register_user_biometrics("Alice", v1, "91-1111-2222-3333")
        id2 = self.matcher.register_user_biometrics("Bob", v2, "91-4444-5555-6666")
        
        # Scenario 1: Probe Alice with low noise (should succeed)
        probe_alice = self.matcher.generate_probe_encoding(v1, noise_level=0.03)
        matched_user, distance = self.matcher.identify_user(probe_alice)
        
        self.assertIsNotNone(matched_user)
        self.assertEqual(matched_user["full_name"], "Alice")
        self.assertEqual(matched_user["abha_number"], "91-1111-2222-3333")
        self.assertTrue(distance < 0.6)

        # Scenario 2: Probe Bob with low noise (should succeed)
        probe_bob = self.matcher.generate_probe_encoding(v2, noise_level=0.03)
        matched_user, distance = self.matcher.identify_user(probe_bob)
        
        self.assertIsNotNone(matched_user)
        self.assertEqual(matched_user["full_name"], "Bob")
        self.assertTrue(distance < 0.6)

        # Scenario 3: Unknown probe (completely random vector)
        # Should either return None (because min distance > 0.6)
        probe_unknown = self.matcher.generate_random_encoding()
        matched_user, distance = self.matcher.identify_user(probe_unknown)
        
        # If it returns a match, the distance must be greater than threshold
        if matched_user is not None:
            self.assertTrue(distance > 0.6, f"Distance {distance} was below threshold for random person")
        else:
            # Correct behavior: no match returned below threshold
            self.assertTrue(distance > 0.6)


class TestABHAClient(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        import database.connection
        import database.abha_db
        cls.orig_abha_path = database.abha_db.ABHA_DB_PATH
        database.abha_db.ABHA_DB_PATH = "test_abha.db"
        database.connection.ABHA_DB_PATH = "test_abha.db"

    @classmethod
    def tearDownClass(cls):
        import database.connection
        import database.abha_db
        database.abha_db.ABHA_DB_PATH = cls.orig_abha_path
        database.connection.ABHA_DB_PATH = cls.orig_abha_path
        if os.path.exists("test_abha.db"):
            try:
                os.remove("test_abha.db")
            except OSError:
                pass

    def setUp(self):
        clear_abha_db()
        seed_abha_db()
        self.client = ABHAClient()

    def test_get_patient_profile(self):
        # Suresh Kumar's record is seeded by default
        profile = self.client.get_patient_profile("91-1111-2222-3333")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["full_name"], "Suresh Kumar")
        self.assertEqual(profile["abha_address"], "suresh.kumar@abdm")
        
        # Non-existent ABHA
        self.assertIsNone(self.client.get_patient_profile("91-0000-0000-0000"))

    def test_invalid_abha_format(self):
        with self.assertRaises(ValueError):
            self.client.get_patient_profile("123") # short length
            
        with self.assertRaises(ValueError):
            self.client.get_patient_profile("91-aaaa-bbbb-cccc") # non-digits

    def test_register_and_fetch(self):
        new_user = self.client.register_new_abha(
            full_name="Karan Johar",
            date_of_birth="1972-05-25",
            gender="M",
            mobile_number="9876123456",
            preferred_address_prefix="karan_j"
        )
        
        abha_number = new_user["abha_number"]
        self.assertIsNotNone(abha_number)
        
        # Verify it can be retrieved
        profile = self.client.get_patient_profile(abha_number)
        self.assertIsNotNone(profile)
        self.assertEqual(profile["full_name"], "Karan Johar")
        self.assertEqual(profile["date_of_birth"], "1972-05-25")
        
        # Verify preferred address
        self.assertEqual(profile["abha_address"], "karan_j@abdm")


if __name__ == "__main__":
    unittest.main()
