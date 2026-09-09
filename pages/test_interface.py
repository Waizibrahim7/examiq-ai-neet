from __future__ import annotations

import json
import time
from pathlib import Path

import streamlit as st

from database import create_or_resume_attempt, get_attempt, save_attempt, submit_attempt
from neet_catalog import (
    get_neet_paper,
    get_neet_papers,
    is_section_b_question,
    question_bank_path,
    section_label,
    source_pdf_path,
)
from result_engine import load_answer_key
from student_store import current_student
from ui_theme import apply_global_styles
from utils.evaluation import is_bonus_question


BASE_DIR = Path(__file__).resolve().parents[1]
OPTION_VALUES = ("1", "2", "3", "4")


def initialize_test_state() -> None:
    for key, value in {
        "active_attempt_id": None,
        "current_question": 1,
        "answers": {},
        "marked_for_review": [],
    }.items():
        st.session_state.setdefault(key, value)


@st.cache_data(show_spinner=False)
def load_question_bank(paper_id: str) -> list[dict]:
    paper = get_neet_paper(paper_id)
    if not paper:
        return []
    path = question_bank_path(paper)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as question_bank_file:
        return json.load(question_bank_file)


def paper_is_ready(paper: dict) -> tuple[bool, str]:
    question_count = len(load_question_bank(paper["paper_id"]))
    answer_count = len(load_answer_key(paper["paper_id"]))
    if question_count != paper["questions"]:
        return False, f"Question display coverage: {question_count}/{paper['questions']}"
    if answer_count != paper["questions"]:
        return False, f"Answer-key coverage: {answer_count}/{paper['questions']}"
    return True, "Question display and answer key validated"


def format_paper_label(paper: dict) -> str:
    return f"{paper['session']} ({paper['questions']} questions)"


def activate_attempt(student: dict, paper: dict) -> None:
    attempt = create_or_resume_attempt(student["email"], paper)
    st.session_state.active_attempt_id = attempt["attempt_id"]
    st.session_state.current_question = 1
    st.session_state.answers = attempt["answers"]
    st.session_state.marked_for_review = attempt["marked_for_review"]


def active_attempt_for_student(student: dict) -> dict | None:
    attempt_id = st.session_state.get("active_attempt_id")
    if not attempt_id:
        return None
    attempt = get_attempt(attempt_id, student["email"])
    if not attempt or attempt["submitted"]:
        return None
    return attempt


def clear_active_session() -> None:
    st.session_state.active_attempt_id = None
    st.session_state.current_question = 1
    st.session_state.answers = {}
    st.session_state.marked_for_review = []


def get_remaining_seconds(attempt: dict) -> int:
    elapsed_seconds = int(time.time() - float(attempt["started_at"]))
    return max(0, int(attempt["duration_seconds"]) - elapsed_seconds)


def format_time(seconds: int) -> str:
    seconds = max(0, seconds)
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


@st.fragment(run_every="1s")
def render_live_timer(attempt: dict) -> None:
    remaining = get_remaining_seconds(attempt)
    st.metric("Time Left", format_time(remaining))
    if 0 < remaining <= 300:
        st.warning("Five minutes remaining. Save your work and review marked questions.")


def answer_status(question_number: int) -> str:
    if str(question_number) in st.session_state.marked_for_review:
        return "Review"
    if str(question_number) in st.session_state.answers:
        return "Answered"
    return "Not answered"


def palette_label(question_number: int) -> str:
    symbol = {"Answered": "●", "Review": "◐", "Not answered": "○"}[answer_status(question_number)]
    return f"{symbol} {question_number}"


def render_question_palette(paper: dict, attempt: dict) -> None:
    st.sidebar.subheader("Question Palette")
    st.sidebar.caption("● Answered  ◐ Marked for review  ○ Not answered")
    total_questions = int(paper["questions"])
    for row_start in range(1, total_questions + 1, 5):
        columns = st.sidebar.columns(5)
        for offset, column in enumerate(columns):
            question_number = row_start + offset
            if question_number > total_questions:
                continue
            button_type = "primary" if question_number == st.session_state.current_question else "secondary"
            if column.button(
                palette_label(question_number),
                key=f"palette_{attempt['attempt_id']}_{question_number}",
                type=button_type,
                help=answer_status(question_number),
            ):
                st.session_state.current_question = question_number
                st.rerun()


def render_exam_status(paper: dict, attempt: dict) -> None:
    total_questions = int(paper["questions"])
    attempted = len(st.session_state.answers)
    review_count = len(st.session_state.marked_for_review)
    st.sidebar.subheader("Test Status")
    st.sidebar.write(f"**Paper:** {paper['session']}")
    st.sidebar.write(f"**Attempted:** {attempted} / {total_questions}")
    st.sidebar.write(f"**Marked for review:** {review_count}")
    st.sidebar.write(f"**Remaining:** {total_questions - attempted}")
    st.sidebar.caption(paper["format_note"])
    render_question_palette(paper, attempt)


def current_question_data(paper: dict) -> dict:
    question_bank = load_question_bank(paper["paper_id"])
    question_number = st.session_state.current_question
    return next(item for item in question_bank if item["question_number"] == question_number)


def section_b_limit_reached(paper: dict, question_number: int) -> bool:
    if not is_section_b_question(paper, question_number):
        return False
    if str(question_number) in st.session_state.answers:
        return False

    same_section = [
        number
        for number in range(1, paper["questions"] + 1)
        if is_section_b_question(paper, number) and section_label(paper, number) == section_label(paper, question_number)
    ]
    answered = sum(1 for number in same_section if str(number) in st.session_state.answers)
    return answered >= 10


def save_current_answer(student: dict, attempt: dict, paper: dict, selected_answer: str | None) -> bool:
    question_key = str(st.session_state.current_question)
    if selected_answer and section_b_limit_reached(paper, st.session_state.current_question):
        st.warning("This Section B already has 10 saved responses. Clear one response before adding another.")
        return False

    if selected_answer:
        st.session_state.answers[question_key] = selected_answer
    else:
        st.session_state.answers.pop(question_key, None)

    saved = save_attempt(
        attempt["attempt_id"],
        student["email"],
        st.session_state.answers,
        st.session_state.marked_for_review,
    )
    if not saved:
        st.error("This attempt is no longer editable. Please return to your result dashboard.")
    return saved


def mark_for_review(student: dict, attempt: dict, paper: dict, selected_answer: str | None) -> None:
    question_key = str(st.session_state.current_question)
    if question_key not in st.session_state.marked_for_review:
        st.session_state.marked_for_review.append(question_key)
    save_current_answer(student, attempt, paper, selected_answer)


def clear_response(student: dict, attempt: dict) -> None:
    question_key = str(st.session_state.current_question)
    st.session_state.answers.pop(question_key, None)
    save_attempt(
        attempt["attempt_id"],
        student["email"],
        st.session_state.answers,
        st.session_state.marked_for_review,
    )


def render_question(student: dict, attempt: dict, paper: dict) -> None:
    question = current_question_data(paper)
    question_number = question["question_number"]
    total_questions = int(paper["questions"])
    st.subheader(f"Question {question_number} of {total_questions}")
    st.caption(section_label(paper, question_number))
    if is_section_b_question(paper, question_number):
        st.info("Section B: choose up to 10 questions in this subject section. Only the first 10 saved responses are evaluated.")
    if is_bonus_question(load_answer_key(paper["paper_id"]).get(question_number)):
        st.info("This question was dropped in the final key. It receives full bonus marks and will not affect your accuracy.")

    image_paths = question.get("image_paths") or [question.get("image_path")]
    for relative_path in image_paths:
        if relative_path:
            path = BASE_DIR / relative_path
            if path.exists():
                st.image(str(path), width="stretch")
            else:
                st.error("A validated question image is missing. This paper has been blocked from testing.")
                return

    saved_answer = st.session_state.answers.get(str(question_number))
    selected_index = OPTION_VALUES.index(saved_answer) if saved_answer in OPTION_VALUES else None
    selected_answer = st.radio(
        "Select your answer",
        OPTION_VALUES,
        index=selected_index,
        format_func=lambda value: f"Option {value}",
        horizontal=True,
        key=f"answer_{attempt['attempt_id']}_{question_number}",
    )

    remaining_seconds = get_remaining_seconds(attempt)
    previous_col, clear_col, save_col, review_col, submit_col = st.columns([1, 1, 1.2, 1.35, 1.1])
    with previous_col:
        if st.button("Previous", disabled=question_number == 1, width="stretch"):
            st.session_state.current_question -= 1
            st.rerun()
    with clear_col:
        if st.button("Clear Response", disabled=not saved_answer or remaining_seconds == 0, width="stretch"):
            clear_response(student, attempt)
            st.rerun()
    with save_col:
        if st.button("Save & Next", disabled=remaining_seconds == 0, type="primary", width="stretch"):
            if save_current_answer(student, attempt, paper, selected_answer):
                if question_number < total_questions:
                    st.session_state.current_question += 1
                st.rerun()
    with review_col:
        if st.button("Mark for Review", disabled=remaining_seconds == 0, width="stretch"):
            mark_for_review(student, attempt, paper, selected_answer)
            st.rerun()
    with submit_col:
        if st.button("Submit Test", type="primary", width="stretch"):
            save_current_answer(student, attempt, paper, selected_answer)
            if submit_attempt(
                attempt["attempt_id"], student["email"], st.session_state.answers, st.session_state.marked_for_review
            ):
                clear_active_session()
                st.switch_page("pages/result_dashboard.py")


def render_original_pdf_download(paper: dict) -> None:
    source_path = source_pdf_path(paper)
    if source_path.exists():
        st.download_button(
            "Download Original PYQ PDF",
            data=source_path.read_bytes(),
            file_name=source_path.name,
            mime="application/pdf",
            width="stretch",
        )


def require_signed_in_student() -> dict | None:
    student = current_student(st.session_state)
    if student:
        return student
    st.warning("Sign in to start a test. Your answers and results are stored in your own account.")
    if st.button("Go to Login", type="primary"):
        st.switch_page("pages/login.py")
    return None


def show_test_interface_page() -> None:
    apply_global_styles()
    st.title("NEET Practice Test")
    st.caption("Attempt a verified PYQ inside ExamIQ AI. Answers are saved only to your student account.")
    initialize_test_state()
    student = require_signed_in_student()
    if not student:
        return

    papers = get_neet_papers()
    papers_by_id = {paper["paper_id"]: paper for paper in papers}
    paper_ids = list(papers_by_id)
    pending_paper_id = st.session_state.pop("pending_paper_id", None)
    selector_key = "test_paper_selector"
    if pending_paper_id in papers_by_id:
        st.session_state[selector_key] = pending_paper_id
    elif st.session_state.get(selector_key) not in papers_by_id:
        st.session_state[selector_key] = paper_ids[0]

    selected_paper_id = st.selectbox(
        "Select NEET Paper",
        paper_ids,
        format_func=lambda paper_id: format_paper_label(papers_by_id[paper_id]),
        key=selector_key,
    )
    selected_paper = papers_by_id[selected_paper_id]
    ready, readiness_message = paper_is_ready(selected_paper)
    st.caption(readiness_message)

    active_attempt = active_attempt_for_student(student)
    control_col_1, control_col_2, control_col_3 = st.columns(3)
    with control_col_1:
        if st.button("Start / Resume Test", type="primary", disabled=not ready, width="stretch"):
            activate_attempt(student, selected_paper)
            st.rerun()
    with control_col_2:
        render_original_pdf_download(selected_paper)
    with control_col_3:
        if st.button("Exit Test", disabled=active_attempt is None, width="stretch"):
            clear_active_session()
            st.rerun()

    if active_attempt and active_attempt["paper_id"] != selected_paper["paper_id"]:
        st.info("A different paper is active. Select that paper to resume it, or start the selected paper separately.")
        return
    if not active_attempt:
        st.info("Choose a verified NEET paper and start the test. Existing drafts resume with their original timer.")
        return

    active_paper = get_neet_paper(active_attempt["paper_id"])
    if not active_paper:
        st.error("The active paper no longer exists in the NEET catalogue.")
        clear_active_session()
        return
    if get_remaining_seconds(active_attempt) == 0:
        submit_attempt(
            active_attempt["attempt_id"], student["email"], st.session_state.answers, st.session_state.marked_for_review
        )
        clear_active_session()
        st.warning("Time is over. Your saved responses have been submitted automatically.")
        st.switch_page("pages/result_dashboard.py")

    render_exam_status(active_paper, active_attempt)
    header_1, header_2, header_3 = st.columns(3)
    header_1.metric("Active Paper", f"NEET {active_paper['year']}")
    header_2.metric("Responses Saved", len(st.session_state.answers))
    with header_3:
        render_live_timer(active_attempt)
    render_question(student, active_attempt, active_paper)


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Practice Test | ExamIQ AI", page_icon="📝", layout="wide")
    show_test_interface_page()
