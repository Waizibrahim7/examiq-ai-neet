import streamlit as st

from database import get_feedback, save_feedback
from student_store import current_student
from ui_theme import apply_global_styles


def average_rating(rows: list[dict]) -> str:
    if not rows:
        return "No ratings yet"
    return f"{sum(row['rating'] for row in rows) / len(rows):.1f} / 5"


def most_requested_feature(rows: list[dict]) -> str:
    suggestions = " ".join(row["suggestions"].lower() for row in rows)
    for phrase, label in (("mock", "More Mock Tests"), ("college", "College Data Coverage"), ("rank", "Rank Dataset Coverage")):
        if phrase in suggestions:
            return label
    return "No suggestion pattern yet"


def show_feedback_page() -> None:
    apply_global_styles()
    st.title("Student Feedback")
    st.caption("Share feedback after your NEET practice experience. Pilot analytics show only actual submitted feedback.")
    student = current_student(st.session_state)
    if not student:
        st.warning("Sign in to submit feedback under your own student account.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/login.py")
        return

    with st.form("feedback_form", clear_on_submit=True):
        rating = st.radio("Rate Your Experience", [1, 2, 3, 4, 5], index=4, format_func=lambda value: "*" * value, horizontal=True)
        difficulty = st.radio("Was the paper difficulty accurate?", ["Easy", "Moderate", "Hard"], index=1, horizontal=True)
        rank_useful = st.radio("Was the rank estimate useful?", ["Yes", "No"], horizontal=True)
        college_helpful = st.radio("Was the college explorer helpful?", ["Yes", "No"], horizontal=True)
        suggestions = st.text_area("Suggestions", placeholder="What should improve in the next pilot release?")
        submitted = st.form_submit_button("Submit Feedback", type="primary")
    if submitted:
        save_feedback(
            student["email"],
            {
                "rating": rating,
                "difficulty": difficulty,
                "rank_useful": rank_useful,
                "college_helpful": college_helpful,
                "suggestions": suggestions,
            },
        )
        st.success("Feedback submitted. Thank you for helping improve the NEET pilot.")

    feedback_rows = get_feedback()
    st.subheader("Pilot Feedback Analytics")
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Average Rating", average_rating(feedback_rows))
    metric_2.metric("Most Requested", most_requested_feature(feedback_rows))
    metric_3.metric("Submitted Feedback", len(feedback_rows))
    if feedback_rows:
        st.dataframe(
            [
                {
                    "Date": row["timestamp"],
                    "Rating": f"{row['rating']} / 5",
                    "Difficulty": row["difficulty"],
                    "Rank Useful": row["rank_useful"],
                    "College Helpful": row["college_helpful"],
                    "Suggestions": row["suggestions"],
                }
                for row in feedback_rows[:10]
            ],
            width="stretch",
            hide_index=True,
        )


if __name__ == "__main__":
    st.set_page_config(page_title="Feedback | ExamIQ AI", page_icon="⭐", layout="wide")
    show_feedback_page()
