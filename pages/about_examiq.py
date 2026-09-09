from pathlib import Path

import streamlit as st

from neet_catalog import answer_key_path, get_neet_papers, question_bank_path
from ui_theme import apply_global_styles


BASE_DIR = Path(__file__).resolve().parents[1]


def show_about_page() -> None:
    apply_global_styles()
    papers = get_neet_papers()
    answer_keys = sum(answer_key_path(paper).exists() for paper in papers)
    question_banks = sum(question_bank_path(paper).exists() for paper in papers)
    cutoff_available = (BASE_DIR / "datasets" / "college_cutoffs" / "college_cutoffs.csv").exists()

    st.title("About ExamIQ AI")
    st.caption("NEET-first student practice pilot")
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Release", "NEET Pilot 0.2")
    metric_2.metric("Framework", "Streamlit")
    metric_3.metric("Student Data", "SQLite")
    metric_4.metric("Verified Papers", len(papers))

    stat_1, stat_2, stat_3, stat_4 = st.columns(4)
    stat_1.metric("Question Banks", f"{question_banks}/{len(papers)}")
    stat_2.metric("Answer Keys", f"{answer_keys}/{len(papers)}")
    stat_3.metric("Prediction Models", "2 planning tools")
    stat_4.metric("College Dataset", "Available" if cutoff_available else "Missing")

    st.subheader("Current Scope")
    st.write("ExamIQ AI currently supports verified NEET PYQ practice, timed attempts, per-student results, subject analytics, practice rank estimation, a historical cutoff explorer, feedback, and pilot administration.")
    st.subheader("Architecture")
    st.code("Student account -> SQLite attempt -> NEET evaluation -> Result & analytics -> Practice rank -> College explorer", language="text")
    st.subheader("Before Public Scale")
    st.warning("This build is ready for controlled student-pilot testing. A 5,000+ concurrent-student launch needs cloud deployment, managed PostgreSQL, object storage, rate limiting, monitoring, backups, and a load test.")


if __name__ == "__main__":
    st.set_page_config(page_title="About ExamIQ AI", page_icon="ℹ", layout="wide")
    show_about_page()
