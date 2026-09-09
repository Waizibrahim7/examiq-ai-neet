"""Create question images from the verified NEET source pages.

The PDF uses two columns. Cropping each question from its own column preserves
the original figures, superscripts, and option text without unreliable OCR.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from neet_catalog import get_neet_papers, question_bank_path, source_pdf_path


QUESTION_IMAGE_DIR = BASE_DIR / "datasets" / "question_images"
QUESTION_NUMBER = re.compile(r"(\d{1,3})\.")


def find_question_starts(document: fitz.Document, paper: dict) -> dict[int, dict]:
    starts: dict[int, dict] = {}
    source_blocks = paper.get("source_blocks") or (
        {
            "pages": paper["source_pages"],
            "source_questions": (1, paper["questions"]),
            "app_question_start": 1,
        },
    )
    for source_block in source_blocks:
        first_page, last_page = source_block["pages"]
        source_start, source_end = source_block["source_questions"]
        app_question_start = source_block["app_question_start"]
        for page_number in range(first_page, last_page + 1):
            page = document[page_number - 1]
            for x0, y0, x1, y1, text, *_ in page.get_text("words", sort=True):
                match = QUESTION_NUMBER.fullmatch(text)
                if not match:
                    continue
                source_question_number = int(match.group(1))
                if not source_start <= source_question_number <= source_end:
                    continue
                question_number = app_question_start + (source_question_number - source_start)
                if question_number in starts:
                    raise ValueError(f"Duplicate question {question_number} in {paper['paper_id']}")
                starts[question_number] = {
                    "page_index": page_number - 1,
                    "x0": x0,
                    "y0": y0,
                    "column": "left" if x0 < page.rect.width / 2 else "right",
                }

    expected = set(range(1, paper["questions"] + 1))
    missing = sorted(expected - set(starts))
    if missing:
        raise ValueError(f"Missing question starts for {paper['paper_id']}: {missing}")
    return starts


def crop_question_images(paper: dict) -> list[dict]:
    pdf_path = source_pdf_path(paper)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    document = fitz.open(pdf_path)
    starts = find_question_starts(document, paper)
    by_page_and_column: dict[tuple[int, str], list[tuple[int, dict]]] = defaultdict(list)
    for question_number, start in starts.items():
        by_page_and_column[(start["page_index"], start["column"])].append((question_number, start))
    for items in by_page_and_column.values():
        items.sort(key=lambda item: item[1]["y0"])

    # The source booklets use a newspaper-style layout: left column top-to-bottom,
    # then right column top-to-bottom. A question at the bottom of the left column
    # can continue above the next question in the right column.
    visual_order = sorted(
        starts.items(),
        key=lambda item: (
            item[1]["page_index"],
            0 if item[1]["column"] == "left" else 1,
            item[1]["y0"],
        ),
    )
    next_visual_start = {
        question_number: visual_order[index + 1][1] if index + 1 < len(visual_order) else None
        for index, (question_number, _) in enumerate(visual_order)
    }

    output_dir = QUESTION_IMAGE_DIR / paper["paper_id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    questions = []
    for question_number in range(1, paper["questions"] + 1):
        start = starts[question_number]
        page = document[start["page_index"]]
        page_width = page.rect.width
        page_height = page.rect.height
        next_start = next_visual_start[question_number]

        def column_bounds(column: str) -> tuple[float, float]:
            if column == "left":
                return 18, (page_width / 2) - 5
            return (page_width / 2) + 5, page_width - 18

        fragments = [(start["column"], max(34, start["y0"] - 8), page_height - 26)]
        if next_start and next_start["page_index"] == start["page_index"]:
            if next_start["column"] == start["column"]:
                fragments = [(start["column"], max(34, start["y0"] - 8), next_start["y0"] - 8)]
            else:
                fragments.append((next_start["column"], 34, next_start["y0"] - 8))

        image_paths = []
        for fragment_index, (column, top, bottom) in enumerate(fragments, start=1):
            left, right = column_bounds(column)
            clip = fitz.Rect(left, top, right, max(top + 30, bottom))
            suffix = "" if len(fragments) == 1 else f"_{fragment_index}"
            image_path = output_dir / f"q{question_number:03d}{suffix}.png"
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), clip=clip, alpha=False)
            pixmap.save(image_path)
            image_paths.append(str(image_path.relative_to(BASE_DIR)))
        questions.append(
            {
                "question_number": question_number,
                "image_paths": image_paths,
                "source_page": start["page_index"] + 1,
                "options": ["1", "2", "3", "4"],
            }
        )

    bank_path = question_bank_path(paper)
    bank_path.parent.mkdir(parents=True, exist_ok=True)
    with bank_path.open("w", encoding="utf-8") as output_file:
        json.dump(questions, output_file, indent=2)
    return questions


def main() -> None:
    for paper in get_neet_papers():
        questions = crop_question_images(paper)
        print(f"{paper['paper_id']}: {len(questions)} question images created")


if __name__ == "__main__":
    main()
