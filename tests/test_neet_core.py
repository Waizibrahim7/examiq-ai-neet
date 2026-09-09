import tempfile
import unittest
from pathlib import Path

import database
from database import create_or_resume_attempt, create_student, get_student_attempts, initialize_database, submit_attempt
from neet_catalog import get_neet_paper
from result_engine import calculate_result
from student_store import authenticate_student, register_student


class NeetCoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        database.DATABASE_PATH = Path(self.temporary_directory.name) / "test.db"
        initialize_database()

    def tearDown(self):
        database.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    def test_student_attempts_are_separate_by_account(self):
        first = create_student(
            {"name": "Student One", "email": "one@example.com", "mobile": "9999999991", "category": "General", "state": "Delhi"},
            "hash-one",
        )
        second = create_student(
            {"name": "Student Two", "email": "two@example.com", "mobile": "9999999992", "category": "General", "state": "Delhi"},
            "hash-two",
        )
        paper = get_neet_paper("neet_ug_2025_code45")
        first_attempt = create_or_resume_attempt(first["email"], paper)
        second_attempt = create_or_resume_attempt(second["email"], paper)
        self.assertNotEqual(first_attempt["attempt_id"], second_attempt["attempt_id"])
        self.assertEqual(len(get_student_attempts(first["email"])), 1)
        self.assertEqual(len(get_student_attempts(second["email"])), 1)

    def test_neet_2024_section_b_scores_180_questions(self):
        answer_key = {question: "1" for question in range(1, 201)}
        answers = {str(question): "1" for question in range(1, 201)}
        result = calculate_result(answers, answer_key, "neet_ug_2024_codet3")
        self.assertEqual(result["total_questions"], 180)
        self.assertEqual(result["score"], 720)
        self.assertEqual(result["max_score"], 720)

    def test_submitted_attempt_cannot_be_overwritten(self):
        student = create_student(
            {"name": "Student", "email": "student@example.com", "mobile": "9999999993", "category": "General", "state": "Delhi"},
            "hash",
        )
        paper = get_neet_paper("neet_ug_2025_code45")
        attempt = create_or_resume_attempt(student["email"], paper)
        self.assertTrue(submit_attempt(attempt["attempt_id"], student["email"], {"1": "1"}, []))
        self.assertFalse(submit_attempt(attempt["attempt_id"], student["email"], {"1": "2"}, []))

    def test_password_authentication_requires_the_registered_password(self):
        register_student(
            {"name": "Authenticated Student", "email": "auth@example.com", "mobile": "9999999994", "category": "General", "state": "Delhi"},
            "StrongPassword1",
        )
        self.assertIsNotNone(authenticate_student("auth@example.com", "StrongPassword1"))
        self.assertIsNone(authenticate_student("auth@example.com", "wrong-password"))

    def test_neet_2023_source_layout_and_dropped_question_are_supported(self):
        paper = get_neet_paper("neet_ug_2023_solved")
        answer_key = {question: "1" for question in range(1, 201)}
        answer_key[108] = "BONUS"
        result = calculate_result({}, answer_key, paper["paper_id"])

        self.assertEqual(paper["questions"], 200)
        self.assertEqual(result["bonus"], 1)
        self.assertEqual(result["score"], 4)
        self.assertEqual(result["max_score"], 720)


if __name__ == "__main__":
    unittest.main()
