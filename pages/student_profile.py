import streamlit as st

from pages.rank_predictor import load_rank_data, predict_air
from result_engine import calculate_result, get_attempts, load_answer_key
from student_store import current_student
from ui_theme import apply_global_styles


def normalized_marks(result: dict) -> int:
    return max(0, min(720, round((result["score"] / result["max_score"]) * 720))) if result["max_score"] else 0


def scored_attempts(student_email: str) -> list[dict]:
    rows = []
    for attempt in get_attempts(student_email):
        if not attempt["submitted"]:
            continue
        answer_key = load_answer_key(attempt["paper_id"])
        if answer_key:
            rows.append({"attempt": attempt, "result": calculate_result(attempt["answers"], answer_key, attempt["paper_id"])})
    return rows


def show_student_profile_page() -> None:
    apply_global_styles()
    st.title("Student Profile")
    st.caption("Your NEET account details, verified test history, and next actions.")
    student = current_student(st.session_state)
    if not student:
        st.warning("Sign in to view your profile.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/login.py")
        return

    attempt_rows = scored_attempts(student["email"])
    scores = [row["result"]["score"] for row in attempt_rows]
    latest_result = attempt_rows[0]["result"] if attempt_rows else None
    predicted_rank = "--"
    if latest_result and latest_result["score"] > 0:
        predicted_rank = f"{predict_air(normalized_marks(latest_result), load_rank_data()):,}"

    st.subheader("Student Details")
    st.dataframe(
        [
            {"Field": "Name", "Value": student["name"]},
            {"Field": "Email", "Value": student["email"]},
            {"Field": "Mobile", "Value": student["mobile"]},
            {"Field": "Exam", "Value": "NEET"},
            {"Field": "Category", "Value": student["category"]},
            {"Field": "State", "Value": student["state"]},
        ],
        width="stretch",
        hide_index=True,
    )

    st.subheader("Overall Statistics")
    stat_1, stat_2, stat_3, stat_4 = st.columns(4)
    stat_1.metric("Submitted Tests", len(attempt_rows))
    stat_2.metric("Average Marks", round(sum(scores) / len(scores), 1) if scores else "--")
    stat_3.metric("Highest Marks", max(scores) if scores else "--")
    stat_4.metric("Practice AIR", predicted_rank)

    st.subheader("Quick Links")
    link_1, link_2, link_3, link_4 = st.columns(4)
    if link_1.button("Start Practice", type="primary", width="stretch"):
        st.switch_page("pages/previous_year_papers.py")
    if link_2.button("Test History", width="stretch"):
        st.switch_page("pages/student_history.py")
    if link_3.button("Performance", width="stretch"):
        st.switch_page("pages/performance_analytics.py")
    if link_4.button("College Explorer", width="stretch"):
        st.switch_page("pages/college_predictor.py")

    st.subheader("Latest Achievement")
    if latest_result:
        achievement_1, achievement_2, achievement_3 = st.columns(3)
        achievement_1.metric("Highest Score", max(scores))
        achievement_2.metric("Best Subject", latest_result["strong_subject"])
        achievement_3.metric("Accuracy", f"{latest_result['accuracy']}%")
    else:
        st.info("Complete a NEET practice test to build your personal achievement summary.")


if __name__ == "__main__":
    st.set_page_config(page_title="Profile | ExamIQ AI", page_icon="👤", layout="wide")
    show_student_profile_page()
