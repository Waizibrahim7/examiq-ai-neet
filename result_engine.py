from __future__ import annotations

import json
from pathlib import Path

from database import get_all_attempts, get_latest_student_attempt, get_student_attempts
from neet_catalog import answer_key_path, get_neet_paper, subject_for_question
from utils.evaluation import accepted_answers, evaluate_test, is_bonus_question, normalize_answer


BASE_DIR = Path(__file__).parent


def get_attempts(student_email: str | None = None) -> list[dict]:
    """Return only one student's attempts unless an admin explicitly requests all attempts."""
    return get_student_attempts(student_email) if student_email else []


def get_all_saved_attempts() -> list[dict]:
    return get_all_attempts()


def get_latest_attempt(student_email: str | None = None) -> dict | None:
    return get_latest_student_attempt(student_email) if student_email else None


def load_answer_key(paper_id: str) -> dict[int, str | list[str]]:
    paper = get_neet_paper(paper_id)
    if not paper:
        return {}

    path = answer_key_path(paper)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as answer_key_file:
        raw_answer_key = json.load(answer_key_file)
    return {int(question_number): answer for question_number, answer in raw_answer_key.items()}


def _has_answer(student_answers: dict, question_number: int) -> bool:
    return normalize_answer(student_answers.get(str(question_number)) or student_answers.get(question_number)) is not None


def evaluated_question_numbers(paper_id: str, student_answers: dict, answer_key: dict[int, str | list[str]]) -> list[int]:
    """Respect NEET 2024's 'attempt any 10 of 15' Section B rule."""
    paper = get_neet_paper(paper_id)
    available = sorted(answer_key)
    if not paper or paper["questions"] != 200:
        return available

    selected: list[int] = []
    section_b_ranges = ((36, 50), (86, 100), (136, 150), (186, 200))
    mandatory_ranges = ((1, 35), (51, 85), (101, 135), (151, 185))
    for start, end in mandatory_ranges:
        selected.extend(question for question in range(start, end + 1) if question in answer_key)

    for start, end in section_b_ranges:
        question_numbers = [question for question in range(start, end + 1) if question in answer_key]
        answered = [question for question in question_numbers if _has_answer(student_answers, question)]
        unattempted = [question for question in question_numbers if question not in answered]
        selected.extend((answered[:10] + unattempted[: max(0, 10 - len(answered))]))

    return sorted(selected)


def calculate_result(
    student_answers: dict,
    answer_key: dict[int, str | list[str]],
    paper_id: str,
) -> dict:
    paper = get_neet_paper(paper_id)
    if not paper:
        raise ValueError("This result cannot be calculated because the paper is not in the NEET catalogue.")

    scored_questions = evaluated_question_numbers(paper_id, student_answers, answer_key)
    scored_key = {question: answer_key[question] for question in scored_questions}
    evaluation = evaluate_test(scored_key, student_answers, marks_correct=4, marks_wrong=-1)
    subject_stats: dict[str, dict[str, int]] = {}

    for question_number, correct_answer in scored_key.items():
        subject = subject_for_question(paper, question_number)
        stats = subject_stats.setdefault(subject, {"correct": 0, "wrong": 0, "unattempted": 0, "bonus": 0, "attempted": 0})
        student_answer = normalize_answer(student_answers.get(str(question_number)) or student_answers.get(question_number))
        if is_bonus_question(correct_answer):
            stats["bonus"] += 1
        elif student_answer is None:
            stats["unattempted"] += 1
        elif student_answer in accepted_answers(correct_answer):
            stats["correct"] += 1
            stats["attempted"] += 1
        else:
            stats["wrong"] += 1
            stats["attempted"] += 1

    subject_rows = []
    for subject in ("Physics", "Chemistry", "Botany", "Zoology"):
        stats = subject_stats.get(subject, {"correct": 0, "wrong": 0, "unattempted": 0, "bonus": 0, "attempted": 0})
        accuracy = round((stats["correct"] / stats["attempted"]) * 100, 1) if stats["attempted"] else 0.0
        subject_rows.append({"subject": subject, "accuracy": accuracy, **stats})

    attempted_subjects = [row for row in subject_rows if row["attempted"]]
    strong_subject = max(attempted_subjects, key=lambda row: row["accuracy"])["subject"] if attempted_subjects else "Not available"
    weak_subject = min(attempted_subjects, key=lambda row: row["accuracy"])["subject"] if attempted_subjects else "Not available"

    return {
        "correct": evaluation["correct"],
        "wrong": evaluation["wrong"],
        "unattempted": evaluation["unattempted"],
        "bonus": evaluation["bonus"],
        "attempted": evaluation["attempted"],
        "total_questions": evaluation["total_questions"],
        "score": evaluation["total_marks"],
        "max_score": paper["max_marks"],
        "accuracy": evaluation["accuracy"],
        "answer_review": evaluation["answer_review"],
        "strong_subject": strong_subject,
        "weak_subject": weak_subject,
        "subject_rows": subject_rows,
        "format_note": paper["format_note"],
    }


def get_result_context(student_email: str | None = None, attempt: dict | None = None) -> dict | None:
    selected_attempt = attempt or get_latest_attempt(student_email)
    if not selected_attempt:
        return None
    answer_key = load_answer_key(selected_attempt["paper_id"])
    if not answer_key:
        return {"attempt": selected_attempt, "answer_key": {}, "result": None}
    return {
        "attempt": selected_attempt,
        "answer_key": answer_key,
        "result": calculate_result(selected_attempt["answers"], answer_key, selected_attempt["paper_id"]),
    }
