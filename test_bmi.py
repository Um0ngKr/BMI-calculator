"""Unit and integration tests for BMI Calculator & Health Tracker."""

import unittest
import os
import tempfile
from bmi_core import (
    calculate_bmi,
    classify_bmi,
    validate_measurements,
    get_ideal_weight_range,
    ValidationError
)
from database import BMIDatabase, DatabaseError


class TestBMICalculationAndClassification(unittest.TestCase):
    """Tests arithmetic accuracy and WHO classifications."""

    def test_calculate_bmi_standard(self):
        # 70 kg, 1.75 m -> 70 / (1.75^2) = 70 / 3.0625 = 22.85714... -> 22.86
        self.assertEqual(calculate_bmi(70.0, 1.75), 22.86)

    def test_calculate_bmi_rounding(self):
        # 60 kg, 1.65 m -> 60 / 2.7225 = 22.0385... -> 22.04
        self.assertEqual(calculate_bmi(60.0, 1.65), 22.04)

    def test_calculate_bmi_invalid_numbers(self):
        with self.assertRaises(ValidationError):
            calculate_bmi(-70.0, 1.75)
        with self.assertRaises(ValidationError):
            calculate_bmi(70.0, 0.0)
        with self.assertRaises(ValidationError):
            calculate_bmi(0.0, 1.75)

    def test_classify_bmi_underweight(self):
        result = classify_bmi(18.49)
        self.assertEqual(result["category"], "Underweight")
        self.assertEqual(result["color"], "#0288D1")

    def test_classify_bmi_normal(self):
        result_lower = classify_bmi(18.5)
        self.assertEqual(result_lower["category"], "Normal")
        self.assertEqual(result_lower["color"], "#2E7D32")

        result_upper = classify_bmi(24.9)
        self.assertEqual(result_upper["category"], "Normal")

    def test_classify_bmi_overweight(self):
        result_lower = classify_bmi(25.0)
        self.assertEqual(result_lower["category"], "Overweight")
        self.assertEqual(result_lower["color"], "#F57F17")

        result_upper = classify_bmi(29.9)
        self.assertEqual(result_upper["category"], "Overweight")

    def test_classify_bmi_obese(self):
        result_lower = classify_bmi(30.0)
        self.assertEqual(result_lower["category"], "Obese")
        self.assertEqual(result_lower["color"], "#D32F2F")

        result_high = classify_bmi(45.2)
        self.assertEqual(result_high["category"], "Obese")

    def test_ideal_weight_range(self):
        min_w, max_w = get_ideal_weight_range(1.75)
        # 18.5 * 1.75^2 = 56.656... -> 56.7
        # 24.9 * 1.75^2 = 76.256... -> 76.3
        self.assertEqual(min_w, 56.7)
        self.assertEqual(max_w, 76.3)


class TestInputValidation(unittest.TestCase):
    """Tests string input validation rules and error messaging."""

    def test_valid_inputs(self):
        w, h = validate_measurements("70.5", "1.75")
        self.assertEqual(w, 70.5)
        self.assertEqual(h, 1.75)

    def test_empty_inputs(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_measurements("", "1.75")
        self.assertIn("cannot be empty", str(ctx.exception))

        with self.assertRaises(ValidationError) as ctx:
            validate_measurements("70", "   ")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_non_numeric_inputs(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_measurements("seventy", "1.75")
        self.assertIn("Invalid weight", str(ctx.exception))

        with self.assertRaises(ValidationError) as ctx:
            validate_measurements("70", "one-point-eight")
        self.assertIn("Invalid height", str(ctx.exception))

    def test_negative_and_zero_inputs(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_measurements("-50", "1.75")
        self.assertIn("greater than 0", str(ctx.exception))

        with self.assertRaises(ValidationError) as ctx:
            validate_measurements("50", "0")
        self.assertIn("greater than 0", str(ctx.exception))

    def test_centimeter_detection_hint(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_measurements("70", "175")
        self.assertIn("appears to be in centimeters", str(ctx.exception))


class TestDatabaseOperations(unittest.TestCase):
    """Tests SQLite multi-user persistence and CRUD operations."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_bmi.db")
        self.db = BMIDatabase(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_list_users(self):
        user_id = self.db.add_user("Alice")
        self.assertIsInstance(user_id, int)

        user_id2 = self.db.add_user("Bob")
        self.assertIsInstance(user_id2, int)

        users = self.db.get_users()
        user_names = [u["name"] for u in users]
        self.assertIn("Alice", user_names)
        self.assertIn("Bob", user_names)

    def test_duplicate_user_raises_error(self):
        self.db.add_user("Charlie")
        with self.assertRaises(DatabaseError):
            self.db.add_user("Charlie")

    def test_records_crud_and_isolation(self):
        alice_id = self.db.add_user("Alice")
        bob_id = self.db.add_user("Bob")

        # Add records for Alice
        rec_id1 = self.db.add_record(alice_id, 65.0, 1.70, 22.49, "Normal", "2026-01-01 10:00:00")
        rec_id2 = self.db.add_record(alice_id, 64.0, 1.70, 22.15, "Normal", "2026-02-01 10:00:00")

        # Add record for Bob
        rec_id3 = self.db.add_record(bob_id, 90.0, 1.80, 27.78, "Overweight", "2026-01-15 10:00:00")

        # Test isolation
        alice_records = self.db.get_records_for_user(alice_id)
        self.assertEqual(len(alice_records), 2)
        self.assertEqual(alice_records[0]["bmi"], 22.49)
        self.assertEqual(alice_records[1]["bmi"], 22.15)

        bob_records = self.db.get_records_for_user(bob_id)
        self.assertEqual(len(bob_records), 1)
        self.assertEqual(bob_records[0]["bmi"], 27.78)

        # Test delete record
        deleted = self.db.delete_record(rec_id1)
        self.assertTrue(deleted)
        self.assertEqual(len(self.db.get_records_for_user(alice_id)), 1)

    def test_export_to_csv(self):
        user_id = self.db.add_user("Diana")
        self.db.add_record(user_id, 55.0, 1.62, 20.95, "Normal", "2026-03-01 12:00:00")

        csv_file = os.path.join(self.temp_dir.name, "export.csv")
        count = self.db.export_records_to_csv(user_id, csv_file)
        self.assertEqual(count, 1)

        self.assertTrue(os.path.exists(csv_file))
        with open(csv_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)  # Header + 1 record
            self.assertIn("ID,Timestamp,Weight (kg),Height (m),BMI,Category", lines[0].strip())
            self.assertIn("20.95", lines[1])
            self.assertIn("Normal", lines[1])


if __name__ == "__main__":
    unittest.main()
