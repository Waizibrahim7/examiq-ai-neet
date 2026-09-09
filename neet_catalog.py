"""Verified NEET paper catalogue used by the student-facing application."""

from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# The original upload filenames were checked against the headers inside the PDFs.
# Keep source filenames here so a later rename cannot silently change a live paper.
NEET_PAPERS = (
    {
        "paper_id": "neet_ug_2023_solved",
        "exam": "NEET",
        "year": 2023,
        "session": "NEET UG 2023 - Solved Paper",
        "subject": "Physics, Chemistry, Botany, Zoology",
        "questions": 200,
        "scored_questions": 180,
        "max_marks": 720,
        "duration_seconds": 3 * 60 * 60 + 20 * 60,
        "answer_key_file": "neet_2023.json",
        "source_file": "neet/neet-pyq-2023.pdf",
        "source_pages": (1, 34),
        "source_blocks": (
            {"pages": (1, 11), "source_questions": (1, 100), "app_question_start": 1},
            {"pages": (19, 23), "source_questions": (1, 50), "app_question_start": 101},
            {"pages": (29, 34), "source_questions": (1, 50), "app_question_start": 151},
        ),
        "answer_source_blocks": (
            {"pages": (12, 18), "source_questions": (1, 100), "app_question_start": 1},
            {"pages": (24, 28), "source_questions": (1, 50), "app_question_start": 101},
            {"pages": (35, 38), "source_questions": (1, 50), "app_question_start": 151},
        ),
        "subject_ranges": (
            (1, 50, "Botany"),
            (51, 100, "Zoology"),
            (101, 150, "Physics"),
            (151, 200, "Chemistry"),
        ),
        "format_note": "200 questions; choose 10 of 15 in each Section B",
    },
    {
        "paper_id": "neet_ug_2025_code45",
        "exam": "NEET",
        "year": 2025,
        "session": "NEET UG 2025 - Code 45",
        "subject": "Physics, Chemistry, Botany, Zoology",
        "questions": 180,
        "scored_questions": 180,
        "max_marks": 720,
        "duration_seconds": 3 * 60 * 60,
        "answer_key_file": "neet_2024.json",
        "source_file": "neet/neet-pyq-2024.pdf",
        "source_pages": (2, 25),
        "format_note": "180 compulsory questions",
    },
    {
        "paper_id": "neet_ug_2024_codet3",
        "exam": "NEET",
        "year": 2024,
        "session": "NEET UG 2024 - Code T3",
        "subject": "Physics, Chemistry, Botany, Zoology",
        "questions": 200,
        "scored_questions": 180,
        "max_marks": 720,
        "duration_seconds": 3 * 60 * 60 + 20 * 60,
        "answer_key_file": "neet_2025.json",
        "source_file": "neet/neet-pyq-2025.pdf",
        "source_pages": (2, 27),
        "format_note": "200 questions; choose 10 of 15 in each Section B",
    },
)


def get_neet_papers() -> list[dict]:
    return [dict(paper) for paper in NEET_PAPERS]


def get_neet_paper(paper_id: str) -> dict | None:
    for paper in NEET_PAPERS:
        if paper["paper_id"] == paper_id:
            return dict(paper)
    return None


def source_pdf_path(paper: dict) -> Path:
    return BASE_DIR / "previous_year_papers" / paper["source_file"]


def answer_key_path(paper: dict) -> Path:
    return BASE_DIR / "datasets" / "answer_keys" / paper["answer_key_file"]


def question_bank_path(paper: dict) -> Path:
    return BASE_DIR / "datasets" / "question_banks" / f"{paper['paper_id']}.json"


def subject_for_question(paper: dict, question_number: int) -> str:
    for start, end, subject in paper.get("subject_ranges", ()):
        if start <= question_number <= end:
            return subject

    if paper["questions"] == 180:
        if question_number <= 45:
            return "Physics"
        if question_number <= 90:
            return "Chemistry"
        if question_number <= 135:
            return "Botany"
        return "Zoology"

    if question_number <= 50:
        return "Physics"
    if question_number <= 100:
        return "Chemistry"
    if question_number <= 150:
        return "Botany"
    return "Zoology"


def is_section_b_question(paper: dict, question_number: int) -> bool:
    if paper["questions"] != 200:
        return False

    return any(start <= question_number <= end for start, end in ((36, 50), (86, 100), (136, 150), (186, 200)))


def section_label(paper: dict, question_number: int) -> str:
    subject = subject_for_question(paper, question_number)
    if is_section_b_question(paper, question_number):
        return f"{subject} - Section B"
    return f"{subject} - Section A"
