"""Extract answer keys from the answer-explanation pages of verified NEET PDFs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from neet_catalog import get_neet_paper, source_pdf_path


ANSWER_LINE = re.compile(r"(?m)^\s*(\d{1,3})\.\s*\(([a-dA-D]|None)\)")
LETTER_TO_OPTION = {"a": "1", "b": "2", "c": "3", "d": "4"}


def extract_neet_2023_answer_key() -> dict[str, str]:
    paper = get_neet_paper("neet_ug_2023_solved")
    if not paper:
        raise ValueError("NEET 2023 is missing from the catalogue.")

    document = fitz.open(source_pdf_path(paper))
    answer_key: dict[str, str] = {}
    for source_block in paper["answer_source_blocks"]:
        first_page, last_page = source_block["pages"]
        source_start, source_end = source_block["source_questions"]
        app_question_start = source_block["app_question_start"]
        text = "\n".join(document[page_number - 1].get_text() for page_number in range(first_page, last_page + 1))
        matches = dict(ANSWER_LINE.findall(text))
        expected = {str(question_number) for question_number in range(source_start, source_end + 1)}
        if set(matches) != expected:
            missing = sorted(expected - set(matches), key=int)
            extra = sorted(set(matches) - expected, key=int)
            raise ValueError(f"Invalid NEET 2023 answer block: missing={missing}, extra={extra}")

        for source_number, answer in matches.items():
            question_number = app_question_start + (int(source_number) - source_start)
            answer_key[str(question_number)] = "BONUS" if answer == "None" else LETTER_TO_OPTION[answer.lower()]

    if len(answer_key) != paper["questions"]:
        raise ValueError(f"Expected {paper['questions']} NEET 2023 answers; found {len(answer_key)}.")
    return answer_key


def main() -> None:
    answer_key = extract_neet_2023_answer_key()
    output_path = BASE_DIR / "datasets" / "answer_keys" / "neet_2023.json"
    output_path.write_text(json.dumps(answer_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Saved {len(answer_key)} NEET 2023 answers to {output_path}")


if __name__ == "__main__":
    main()
