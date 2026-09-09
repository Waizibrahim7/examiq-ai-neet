from __future__ import annotations

from datetime import datetime

import streamlit as st

from neet_catalog import get_neet_papers
from pages.rank_predictor import load_rank_data, predict_air
from result_engine import calculate_result, get_attempts, get_latest_attempt, load_answer_key
from student_store import current_student
from ui_theme import apply_global_styles


def normalized_marks(result: dict) -> int:
    return max(0, min(720, round((result["score"] / result["max_score"]) * 720))) if result["max_score"] else 0


def estimate_air(result: dict) -> str:
    if result["score"] <= 0:
        return "--"
    return f"{predict_air(normalized_marks(result), load_rank_data()):,}"


def attempt_label(attempt: dict) -> str:
    status = "Submitted" if attempt["submitted"] else "Draft"
    return f"{attempt['session']} | {attempt['updated_at']} | {status}"


def status_badge(status: str) -> str:
    return {"Correct": "Correct", "Wrong": "Wrong", "Unattempted": "Unattempted", "Bonus": "Bonus"}.get(status, status)


def build_report_pdf(attempt: dict, result: dict, predicted_air: str) -> bytes:
    report_lines = [
        "ExamIQ AI - NEET Practice Result",
        f"Paper: {attempt['session']}",
        f"Submitted: {attempt['updated_at']}",
        f"Marks: {result['score']}/{result['max_score']}",
        f"Accuracy: {result['accuracy']}%",
        f"Correct: {result['correct']}",
        f"Wrong: {result['wrong']}",
        f"Unattempted: {result['unattempted']}",
        f"Bonus questions: {result.get('bonus', 0)}",
        f"Practice Rank Estimate: {predicted_air}",
        f"Strong Subject: {result['strong_subject']}",
        f"Focus Subject: {result['weak_subject']}",
        "This is a practice report, not an NTA scorecard or admission guarantee.",
    ]
    content = ["BT", "/F1 14 Tf", "54 760 Td"]
    for index, line in enumerate(report_lines):
        safe_line = line.replace("(", "[").replace(")", "]")
        if index:
            content.append("0 -28 Td")
        content.append(f"({safe_line}) Tj")
    content.append("ET")
    stream = "\n".join(content).encode("utf-8")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        b"5 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj",
    ]
    body = [b"%PDF-1.4\n"]
    offsets = []
    for item in objects:
        offsets.append(sum(len(part) for part in body))
        body.append(item + b"\n")
    xref_offset = sum(len(part) for part in body)
    body.append(f"xref\n0 {len(objects) + 1}\n".encode())
    body.append(b"0000000000 65535 f \n")
    body.extend(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    body.append(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode())
    return b"".join(body)


def paper_status_rows(attempts: list[dict]) -> list[dict]:
    attempted_ids = {attempt["paper_id"] for attempt in attempts}
    rows = []
    for paper in get_neet_papers():
        answer_key = load_answer_key(paper["paper_id"])
        rows.append(
            {
                "Paper": paper["session"],
                "Question Coverage": f"{paper['questions']} / {paper['questions']}",
                "Answer Key Coverage": f"{len(answer_key)} / {paper['questions']}",
                "Your Status": "Attempt available" if paper["paper_id"] in attempted_ids else "Not attempted",
            }
        )
    return rows


def show_result(attempt: dict, result: dict) -> None:
    predicted_air = estimate_air(result)
    st.session_state.latest_result = result
    st.session_state.latest_attempt = attempt
    st.session_state.prefill_marks = normalized_marks(result)
    if predicted_air != "--":
        st.session_state.prefill_air = int(predicted_air.replace(",", ""))

    st.subheader(attempt["session"])
    st.caption(f"Submitted attempt saved on {attempt['updated_at']}. {result['format_note']}.")
    card_1, card_2, card_3, card_4, card_5, card_6 = st.columns(6)
    card_1.metric("Marks", f"{result['score']}/{result['max_score']}")
    card_2.metric("Accuracy", f"{result['accuracy']}%")
    card_3.metric("Correct", result["correct"])
    card_4.metric("Wrong", result["wrong"])
    card_5.metric("Bonus", result.get("bonus", 0))
    card_6.metric("Practice AIR", predicted_air)

    summary_1, summary_2, summary_3 = st.columns(3)
    summary_1.metric("Attempted", result["attempted"])
    summary_2.metric("Unattempted", result["unattempted"])
    summary_3.metric("Questions Evaluated", result["total_questions"])

    strong_col, weak_col = st.columns(2)
    strong_col.success(f"Strongest attempted subject: {result['strong_subject']}")
    weak_col.warning(f"Focus next on: {result['weak_subject']}")

    st.subheader("Subject Performance")
    st.dataframe(
        [
            {
                "Subject": row["subject"],
                "Correct": row["correct"],
                "Wrong": row["wrong"],
                "Unattempted": row["unattempted"],
                "Bonus": row.get("bonus", 0),
                "Accuracy": f"{row['accuracy']}%",
            }
            for row in result["subject_rows"]
        ],
        width="stretch",
        hide_index=True,
    )

    st.subheader("Response Review")
    st.dataframe(
        [
            {
                "Question": row["question"],
                "Your Answer": row["student_answer"],
                "Correct Answer": row["correct_answer"],
                "Status": status_badge(row["status"]),
            }
            for row in result["answer_review"]
        ],
        width="stretch",
        hide_index=True,
    )

    st.subheader("Next Steps")
    action_1, action_2, action_3, action_4, action_5 = st.columns(5)
    action_1.download_button(
        "Download Report",
        data=build_report_pdf(attempt, result, predicted_air),
        file_name=f"examiq_neet_{attempt['year']}_result.pdf",
        mime="application/pdf",
        width="stretch",
    )
    if action_2.button("Performance", width="stretch"):
        st.switch_page("pages/performance_analytics.py")
    if action_3.button("Rank Estimate", width="stretch"):
        st.switch_page("pages/rank_predictor.py")
    if action_4.button("College Explorer", width="stretch"):
        st.switch_page("pages/college_predictor.py")
    if action_5.button("Retake Paper", width="stretch"):
        st.session_state.pending_paper_id = attempt["paper_id"]
        st.switch_page("pages/test_interface.py")


def show_result_dashboard_page() -> None:
    apply_global_styles()
    st.title("NEET Result Dashboard")
    st.caption("Scores are calculated from your submitted responses and the answer key for the exact selected NEET paper.")
    student = current_student(st.session_state)
    if not student:
        st.warning("Sign in to view your saved results.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/login.py")
        return

    attempts = get_attempts(student["email"])
    st.subheader("Paper Readiness")
    st.dataframe(paper_status_rows(attempts), width="stretch", hide_index=True)
    submitted_attempts = [attempt for attempt in attempts if attempt["submitted"]]
    if not submitted_attempts:
        st.info("You have not submitted a NEET practice test yet.")
        if st.button("Browse NEET Papers", type="primary"):
            st.switch_page("pages/previous_year_papers.py")
        return

    labels = {attempt_label(attempt): attempt for attempt in submitted_attempts}
    label_list = list(labels)
    latest_attempt = get_latest_attempt(student["email"])
    default_index = next(
        (index for index, label in enumerate(label_list) if labels[label]["attempt_id"] == latest_attempt["attempt_id"]), 0
    )
    selected_attempt = labels[st.selectbox("Select Submitted Attempt", label_list, index=default_index)]
    answer_key = load_answer_key(selected_attempt["paper_id"])
    if not answer_key:
        st.error("The answer key for this paper is unavailable, so marks cannot be shown.")
        return
    show_result(selected_attempt, calculate_result(selected_attempt["answers"], answer_key, selected_attempt["paper_id"]))


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Results | ExamIQ AI", page_icon="📊", layout="wide")
    show_result_dashboard_page()
