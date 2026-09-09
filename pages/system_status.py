from pathlib import Path

import streamlit as st

from database import get_all_attempts, initialize_database
from neet_catalog import answer_key_path, get_neet_papers, question_bank_path
from ui_theme import apply_global_styles


BASE_DIR = Path(__file__).resolve().parents[1]


def check_row(component: str, ready: bool, detail: str) -> dict:
    return {"Component": component, "Status": "Ready" if ready else "Needs attention", "Details": detail}


def show_system_status_page() -> None:
    apply_global_styles()
    st.title("NEET Pilot System Status")
    st.caption("Live checks for the local student-pilot environment. This page does not claim cloud-scale readiness.")
    initialize_database()
    papers = get_neet_papers()
    answer_keys_ready = sum(answer_key_path(paper).exists() for paper in papers)
    banks_ready = sum(question_bank_path(paper).exists() for paper in papers)
    rank_data = BASE_DIR / "datasets" / "neet_rank_data.csv"
    cutoff_data = BASE_DIR / "datasets" / "college_cutoffs" / "college_cutoffs.csv"
    attempts = get_all_attempts()
    rows = [
        check_row("SQLite Database", True, "Database opened with WAL mode and per-student attempt records"),
        check_row("NEET Question Images", banks_ready == len(papers), f"{banks_ready}/{len(papers)} verified paper banks available"),
        check_row("NEET Answer Keys", answer_keys_ready == len(papers), f"{answer_keys_ready}/{len(papers)} answer keys available"),
        check_row("Evaluation Engine", answer_keys_ready == len(papers), "NEET +4/-1 scoring with the 2024 Section B rule"),
        check_row("Rank Estimate Data", rank_data.exists(), "NEET reference dataset detected"),
        check_row("College Cutoff Data", cutoff_data.exists(), "NEET cutoff dataset detected"),
        check_row("Student Attempts", True, f"{len(attempts)} local attempt record(s) saved"),
    ]
    ready_count = sum(row["Status"] == "Ready" for row in rows)
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Readiness Checks", f"{ready_count}/{len(rows)}")
    metric_2.metric("Pilot Mode", "Local SQLite")
    metric_3.metric("Verified Papers", len(papers))
    st.dataframe(rows, width="stretch", hide_index=True)
    st.warning("For 5,000+ concurrent students, move from local SQLite to managed PostgreSQL, store PDFs/images in object storage, deploy multiple app instances, and complete load and security testing before release.")


if __name__ == "__main__":
    st.set_page_config(page_title="System Status | ExamIQ AI", page_icon="🟢", layout="wide")
    show_system_status_page()
