import os

import streamlit as st

from database import get_feedback, get_students
from neet_catalog import answer_key_path, get_neet_papers, question_bank_path
from result_engine import get_all_saved_attempts
from student_store import current_student
from ui_theme import apply_global_styles


def has_admin_access(student: dict | None) -> bool:
    configured_email = os.getenv("EXAMIQ_ADMIN_EMAIL", "").strip().lower()
    return bool(student and configured_email and student["email"].lower() == configured_email)


def show_admin_panel_page() -> None:
    apply_global_styles()
    st.title("NEET Pilot Administration")
    st.caption("Operational view for the configured ExamIQ AI administrator.")
    student = current_student(st.session_state)
    if not has_admin_access(student):
        st.warning("Admin access is restricted. Configure EXAMIQ_ADMIN_EMAIL to the email address of the administrator before starting Streamlit.")
        return

    papers = get_neet_papers()
    students = get_students()
    attempts = get_all_saved_attempts()
    feedback_rows = get_feedback()
    answer_key_count = sum(answer_key_path(paper).exists() for paper in papers)
    question_bank_count = sum(question_bank_path(paper).exists() for paper in papers)

    st.subheader("Pilot Overview")
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Registered Students", len(students))
    metric_2.metric("Verified NEET Papers", len(papers))
    metric_3.metric("Answer Keys", answer_key_count)
    metric_4.metric("Submitted Feedback", len(feedback_rows))

    st.subheader("Content Validation")
    st.dataframe(
        [
            {
                "Paper": paper["session"],
                "Questions": paper["questions"],
                "Question Images": "Ready" if question_bank_path(paper).exists() else "Missing",
                "Answer Key": "Ready" if answer_key_path(paper).exists() else "Missing",
                "Format": paper["format_note"],
            }
            for paper in papers
        ],
        width="stretch",
        hide_index=True,
    )

    st.subheader("Student Activity")
    latest_by_student = {}
    for attempt in attempts:
        latest_by_student.setdefault(attempt["student_email"], attempt)
    student_rows = [
        {
            "Student": row["name"],
            "Email": row["email"],
            "Category": row["category"],
            "State": row["state"],
            "Latest Paper": latest_by_student.get(row["email"], {}).get("session", "No attempt"),
            "Latest Status": "Submitted" if latest_by_student.get(row["email"], {}).get("submitted") else "No submitted test",
        }
        for row in students
    ]
    st.dataframe(student_rows, width="stretch", hide_index=True)

    st.subheader("Pilot Data Controls")
    st.info("File uploads are intentionally disabled in the student pilot. Validate paper source, answer key, and cutoff data offline before adding them to the repository.")
    report_rows = [
        "Metric,Value",
        f"Registered Students,{len(students)}",
        f"Saved Attempts,{len(attempts)}",
        f"Submitted Feedback,{len(feedback_rows)}",
        f"Verified NEET Papers,{len(papers)}",
    ]
    report_col_1, report_col_2 = st.columns(2)
    report_col_1.download_button(
        "Download Pilot Summary",
        data="\n".join(report_rows),
        file_name="examiq_neet_pilot_summary.csv",
        mime="text/csv",
        width="stretch",
    )
    if report_col_2.button("View System Status", width="stretch"):
        st.switch_page("pages/system_status.py")


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Admin | ExamIQ AI", page_icon="⚙", layout="wide")
    show_admin_panel_page()
