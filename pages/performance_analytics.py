import streamlit as st

from pages.rank_predictor import load_rank_data, predict_air
from result_engine import get_result_context
from student_store import current_student
from ui_theme import apply_global_styles


def normalized_marks(result: dict) -> int:
    return max(0, min(720, round((result["score"] / result["max_score"]) * 720))) if result["max_score"] else 0


def show_performance_analytics_page() -> None:
    apply_global_styles()
    st.title("NEET Performance Analytics")
    st.caption("Subject analytics based on your latest submitted NEET practice attempt.")
    student = current_student(st.session_state)
    if not student:
        st.warning("Sign in to see your performance analytics.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/login.py")
        return

    context = get_result_context(student["email"])
    if not context or not context["result"] or not context["attempt"]["submitted"]:
        st.info("Submit a NEET practice test to unlock analytics.")
        if st.button("Start NEET Practice", type="primary"):
            st.switch_page("pages/previous_year_papers.py")
        return

    attempt = context["attempt"]
    result = context["result"]
    predicted_air = "--" if result["score"] <= 0 else f"{predict_air(normalized_marks(result), load_rank_data()):,}"
    st.subheader(attempt["session"])
    card_1, card_2, card_3, card_4 = st.columns(4)
    card_1.metric("Marks", f"{result['score']}/{result['max_score']}")
    card_2.metric("Practice AIR", predicted_air)
    card_3.metric("Accuracy", f"{result['accuracy']}%")
    card_4.metric("Attempted", f"{result['attempted']}/{result['total_questions']}")

    st.subheader("Subject-wise Performance")
    st.dataframe(
        [
            {
                "Subject": row["subject"],
                "Correct": row["correct"],
                "Wrong": row["wrong"],
                "Unattempted": row["unattempted"],
                "Accuracy": f"{row['accuracy']}%",
            }
            for row in result["subject_rows"]
        ],
        width="stretch",
        hide_index=True,
    )
    strong_col, weak_col = st.columns(2)
    strong_col.success(f"Strength: {result['strong_subject']}")
    weak_col.warning(f"Area to improve: {result['weak_subject']}")

    st.subheader("Attempt Quality")
    attempted_ratio = result["attempted"] / result["total_questions"] if result["total_questions"] else 0
    st.write(f"Attempt rate: {result['attempted']} / {result['total_questions']}")
    st.progress(attempted_ratio)
    st.write(f"Accuracy: {result['accuracy']}%")
    st.progress(result["accuracy"] / 100)

    link_1, link_2, link_3 = st.columns(3)
    if link_1.button("Result Dashboard", width="stretch"):
        st.switch_page("pages/result_dashboard.py")
    if link_2.button("Rank Estimate", width="stretch"):
        st.session_state.prefill_marks = normalized_marks(result)
        st.switch_page("pages/rank_predictor.py")
    if link_3.button("College Explorer", width="stretch"):
        st.session_state.prefill_marks = normalized_marks(result)
        if predicted_air != "--":
            st.session_state.prefill_air = int(predicted_air.replace(",", ""))
        st.switch_page("pages/college_predictor.py")


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Analytics | ExamIQ AI", page_icon="📈", layout="wide")
    show_performance_analytics_page()
