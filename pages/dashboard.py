import streamlit as st

from neet_catalog import get_neet_papers
from pages.rank_predictor import load_rank_data, predict_air
from result_engine import get_attempts, get_result_context
from student_store import current_student
from ui_theme import apply_global_styles


def normalized_marks(result: dict) -> int:
    return max(0, min(720, round((result["score"] / result["max_score"]) * 720))) if result["max_score"] else 0


def predicted_air(result: dict) -> str:
    if result["score"] <= 0:
        return "--"
    return f"{predict_air(normalized_marks(result), load_rank_data()):,}"


def show_dashboard_page() -> None:
    apply_global_styles()
    student = current_student(st.session_state)
    st.title("NEET Student Dashboard")
    if not student:
        st.info("Create an account or sign in to store NEET attempts, results, and feedback securely.")
        login_col, register_col = st.columns(2)
        if login_col.button("Student Login", type="primary", width="stretch"):
            st.switch_page("pages/login.py")
        if register_col.button("Create NEET Account", width="stretch"):
            st.switch_page("pages/register.py")
        return

    attempts = get_attempts(student["email"])
    context = get_result_context(student["email"])
    result = context["result"] if context else None
    st.caption(f"Welcome, {student['name']}. Continue where you left off or start a verified NEET PYQ.")

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Verified Papers", len(get_neet_papers()))
    metric_2.metric("Your Attempts", len(attempts))
    metric_3.metric("Latest Marks", f"{result['score']}/{result['max_score']}" if result else "--")
    metric_4.metric("Practice Rank Estimate", predicted_air(result) if result else "--")

    st.subheader("Practice Workflow")
    action_1, action_2, action_3, action_4 = st.columns(4)
    if action_1.button("Browse Papers", type="primary", width="stretch"):
        st.switch_page("pages/previous_year_papers.py")
    if action_2.button("Continue Test", width="stretch"):
        st.switch_page("pages/test_interface.py")
    if action_3.button("View Results", width="stretch"):
        st.switch_page("pages/result_dashboard.py")
    if action_4.button("Performance Analytics", width="stretch"):
        st.switch_page("pages/performance_analytics.py")

    action_5, action_6, action_7, action_8 = st.columns(4)
    if action_5.button("Rank Estimate", width="stretch"):
        if result:
            st.session_state.prefill_marks = normalized_marks(result)
        st.switch_page("pages/rank_predictor.py")
    if action_6.button("College Explorer", width="stretch"):
        if result:
            st.session_state.prefill_marks = normalized_marks(result)
            estimated_rank = predicted_air(result)
            if estimated_rank != "--":
                st.session_state.prefill_air = int(estimated_rank.replace(",", ""))
        st.switch_page("pages/college_predictor.py")
    if action_7.button("My Profile", width="stretch"):
        st.switch_page("pages/student_profile.py")
    if action_8.button("Give Feedback", width="stretch"):
        st.switch_page("pages/feedback.py")

    st.caption("Rank and college outputs are practice estimates based on the currently loaded datasets, not an admission guarantee.")


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Dashboard | ExamIQ AI", page_icon="📘", layout="wide")
    show_dashboard_page()
