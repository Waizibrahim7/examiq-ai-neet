import streamlit as st

from pages.rank_predictor import load_rank_data, predict_air
from result_engine import calculate_result, get_attempts, load_answer_key
from student_store import current_student
from ui_theme import apply_global_styles


def normalized_marks(result: dict) -> int:
    return max(0, min(720, round((result["score"] / result["max_score"]) * 720))) if result["max_score"] else 0


def build_history_rows(student_email: str) -> list[dict]:
    rank_data = load_rank_data()
    rows = []
    for attempt in get_attempts(student_email):
        if not attempt["submitted"]:
            continue
        answer_key = load_answer_key(attempt["paper_id"])
        if not answer_key:
            continue
        result = calculate_result(attempt["answers"], answer_key, attempt["paper_id"])
        rank = "--" if result["score"] <= 0 else f"{predict_air(normalized_marks(result), rank_data):,}"
        rows.append(
            {
                "Paper": attempt["session"],
                "Submitted": attempt["updated_at"],
                "Marks": f"{result['score']}/{result['max_score']}",
                "Accuracy": f"{result['accuracy']}%",
                "Practice AIR": rank,
                "raw_score": result["score"],
            }
        )
    return rows


def show_student_history_page() -> None:
    apply_global_styles()
    st.title("NEET Test History")
    st.caption("Your submitted NEET papers and performance trend. Drafts are kept private until you submit them.")
    student = current_student(st.session_state)
    if not student:
        st.warning("Sign in to see your test history.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/login.py")
        return

    history_rows = build_history_rows(student["email"])
    scores = [row["raw_score"] for row in history_rows]
    stat_1, stat_2, stat_3 = st.columns(3)
    stat_1.metric("Submitted Tests", len(history_rows))
    stat_2.metric("Average Score", round(sum(scores) / len(scores), 1) if scores else "--")
    stat_3.metric("Best Score", max(scores) if scores else "--")

    st.subheader("Previous Tests")
    if history_rows:
        st.dataframe(
            [{key: value for key, value in row.items() if key != "raw_score"} for row in history_rows],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No submitted NEET practice tests yet.")

    st.subheader("Performance Trend")
    if len(scores) >= 2:
        trend_rows = list(reversed(history_rows))
        st.line_chart({"Marks": [row["raw_score"] for row in trend_rows]}, height=260)
    elif scores:
        st.info("One submitted test is saved. Complete another paper to see a trend.")
    else:
        st.info("Your chart appears after you submit a NEET paper.")

    st.subheader("Recommendations")
    recommendations = [
        "Review incorrect responses in the Result Dashboard before retaking a paper.",
        "Use the subject analytics to plan your next revision session.",
        "Treat rank and college outputs as planning estimates, not admission guarantees.",
    ]
    for recommendation in recommendations:
        st.info(recommendation)

    link_1, link_2, link_3 = st.columns(3)
    if link_1.button("Browse Papers", type="primary", width="stretch"):
        st.switch_page("pages/previous_year_papers.py")
    if link_2.button("Performance Analytics", width="stretch"):
        st.switch_page("pages/performance_analytics.py")
    if link_3.button("College Explorer", width="stretch"):
        st.switch_page("pages/college_predictor.py")


if __name__ == "__main__":
    st.set_page_config(page_title="NEET History | ExamIQ AI", page_icon="📚", layout="wide")
    show_student_history_page()
