from __future__ import annotations


SAMPLE_ANSWER_KEY = {
    1: "B",
    2: "A",
    3: "D",
    4: "C",
    5: "B",
}

SAMPLE_STUDENT_ANSWERS = {
    1: "B",
    2: "C",
    3: "D",
    4: "",
    5: "B",
}

LETTER_TO_NUMBER = {
    "A": "1",
    "B": "2",
    "C": "3",
    "D": "4",
}


def normalize_answer(answer: str | int | None) -> str | None:
    if answer is None:
        return None

    clean_answer = str(answer).strip().upper()
    if not clean_answer:
        return None

    clean_answer = clean_answer.replace("OPTION ", "", 1).strip()
    if clean_answer in LETTER_TO_NUMBER:
        return LETTER_TO_NUMBER[clean_answer]

    return clean_answer


def accepted_answers(answer: str | int | list | None) -> set[str]:
    if answer is None:
        return set()

    if isinstance(answer, list):
        values = answer
    else:
        values = str(answer).replace("/", " or ").split(" or ")

    return {normalized for value in values if (normalized := normalize_answer(value))}


def is_bonus_question(answer: str | int | list | None) -> bool:
    """A dropped question awards full marks to every candidate."""
    return isinstance(answer, str) and answer.strip().upper() == "BONUS"


def evaluate_test(
    answer_key: dict[int, str | list[str]],
    student_answers: dict[int | str, str],
    marks_correct: int = 4,
    marks_wrong: int = -1,
) -> dict:
    correct = 0
    wrong = 0
    unattempted = 0
    bonus = 0
    answer_review = []

    for question_number, correct_answer in answer_key.items():
        student_answer = normalize_answer(
            student_answers.get(question_number) or student_answers.get(str(question_number))
        )
        correct_options = accepted_answers(correct_answer)

        if is_bonus_question(correct_answer):
            status = "Bonus"
            bonus += 1
        elif student_answer is None:
            status = "Unattempted"
            unattempted += 1
        elif student_answer in correct_options:
            status = "Correct"
            correct += 1
        else:
            status = "Wrong"
            wrong += 1

        answer_review.append(
            {
                "question": question_number,
                "student_answer": student_answers.get(str(question_number))
                or student_answers.get(question_number)
                or "Not Attempted",
                "correct_answer": correct_answer,
                "status": status,
            }
        )

    attempted = correct + wrong
    total_questions = len(answer_key)
    total_marks = (correct * marks_correct) + (wrong * marks_wrong) + (bonus * marks_correct)
    maximum_marks = total_questions * marks_correct
    accuracy = round((correct / attempted) * 100, 1) if attempted else 0.0

    return {
        "correct": correct,
        "wrong": wrong,
        "unattempted": unattempted,
        "bonus": bonus,
        "attempted": attempted,
        "total_questions": total_questions,
        "total_marks": total_marks,
        "maximum_marks": maximum_marks,
        "accuracy": accuracy,
        "answer_review": answer_review,
    }


if __name__ == "__main__":
    print(evaluate_test(SAMPLE_ANSWER_KEY, SAMPLE_STUDENT_ANSWERS))
