import json
import re
import sys
from pathlib import Path

import fitz


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from pages.previous_year_papers import PAPER_FILES, PAPERS_DIR

ANSWER_KEY_DIR = BASE_DIR / "datasets" / "answer_keys"
ANSWER_LINE_PATTERN = re.compile(r"(\d{1,3})\.\s*\(([^)]+)\)")


def extract_pdf_text(pdf_path: Path) -> str:
    document = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in document)


def clean_answer(answer: str) -> str | list[str]:
    answer = answer.strip()
    if " or " in answer:
        return [part.strip() for part in answer.split(" or ") if part.strip()]
    return answer


def extract_answer_key_from_text(text: str, exam: str) -> dict[str, str | list[str]]:
    if exam == "JEE":
        key_text = text[text.find("ANSWER KEYS") :] if "ANSWER KEYS" in text else text
        matches = ANSWER_LINE_PATTERN.findall(key_text)
        return {question_number: clean_answer(answer) for question_number, answer in matches}

    matches = ANSWER_LINE_PATTERN.findall(text)
    key = {}
    for question_number, answer in matches:
        number = int(question_number)
        if 1 <= number <= 200:
            key[str(number)] = clean_answer(answer)
    return key


def extract_all_answer_keys() -> None:
    ANSWER_KEY_DIR.mkdir(parents=True, exist_ok=True)

    for paper_id, relative_path in PAPER_FILES.items():
        pdf_path = PAPERS_DIR / relative_path
        if not pdf_path.exists():
            continue

        exam = paper_id.split("_", 1)[0].upper()
        answer_key = extract_answer_key_from_text(extract_pdf_text(pdf_path), exam)
        output_path = ANSWER_KEY_DIR / f"{paper_id}.json"

        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(answer_key, output_file, indent=4)

        print(f"{paper_id}: extracted {len(answer_key)} answers")


if __name__ == "__main__":
    extract_all_answer_keys()
