import argparse
import json
import re
from pathlib import Path

import fitz


BASE_DIR = Path(__file__).resolve().parents[1]
PAPERS_DIR = BASE_DIR / "previous_year_papers"
QUESTION_BANK_DIR = BASE_DIR / "datasets" / "question_banks"
QUESTION_IMAGE_DIR = BASE_DIR / "datasets" / "question_images"
QUESTION_PATTERN = re.compile(r"^Q\s*(\d+)\s*[\.:]", re.IGNORECASE)


def find_question_starts(document: fitz.Document) -> list[dict]:
    starts = []

    for page_index in range(document.page_count):
        page = document[page_index]
        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text, *_ = block
            clean_text = " ".join(text.split())
            match = QUESTION_PATTERN.match(clean_text)
            if match:
                starts.append(
                    {
                        "question_number": int(match.group(1)),
                        "page_index": page_index,
                        "y0": y0,
                    }
                )

    return sorted(starts, key=lambda item: item["question_number"])


def clip_for_question(document: fitz.Document, current: dict, next_start: dict | None) -> fitz.Rect:
    page = document[current["page_index"]]
    page_rect = page.rect
    y0 = max(60, current["y0"] - 6)

    if next_start and next_start["page_index"] == current["page_index"]:
        y1 = max(y0 + 40, next_start["y0"] - 8)
    else:
        y1 = min(page_rect.height - 60, 770)

    return fitz.Rect(28, y0, page_rect.width - 28, y1)


def extract_question_bank(paper_id: str, pdf_relative_path: str) -> list[dict]:
    pdf_path = PAPERS_DIR / pdf_relative_path
    output_dir = QUESTION_IMAGE_DIR / paper_id
    output_dir.mkdir(parents=True, exist_ok=True)
    QUESTION_BANK_DIR.mkdir(parents=True, exist_ok=True)

    document = fitz.open(pdf_path)
    starts = find_question_starts(document)
    questions = []

    for index, start in enumerate(starts):
        next_start = starts[index + 1] if index + 1 < len(starts) else None
        page = document[start["page_index"]]
        clip = clip_for_question(document, start, next_start)
        image_name = f"q{start['question_number']:03d}.png"
        image_path = output_dir / image_name
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip, alpha=False)
        pixmap.save(image_path)

        questions.append(
            {
                "question_number": start["question_number"],
                "question": f"Question {start['question_number']} extracted from {paper_id}",
                "image_path": str(image_path.relative_to(BASE_DIR)),
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "source_page": start["page_index"] + 1,
            }
        )

    question_bank_path = QUESTION_BANK_DIR / f"{paper_id}.json"
    with question_bank_path.open("w", encoding="utf-8") as output_file:
        json.dump(questions, output_file, indent=4)

    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract question images from a PYQ PDF.")
    parser.add_argument("paper_id")
    parser.add_argument("pdf_relative_path")
    args = parser.parse_args()

    questions = extract_question_bank(args.paper_id, args.pdf_relative_path)
    print(f"Extracted {len(questions)} questions for {args.paper_id}")


if __name__ == "__main__":
    main()
