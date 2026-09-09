from __future__ import annotations

import streamlit as st

from neet_catalog import answer_key_path, get_neet_papers, question_bank_path, source_pdf_path
from ui_theme import apply_global_styles


def paper_readiness(paper: dict) -> str:
    question_bank = question_bank_path(paper)
    question_count = 0
    if question_bank.exists():
        import json

        question_count = len(json.loads(question_bank.read_text(encoding="utf-8")))
    answer_count = 0
    if answer_key_path(paper).exists():
        import json

        answer_count = len(json.loads(answer_key_path(paper).read_text(encoding="utf-8")))
    if question_count == paper["questions"] and answer_count == paper["questions"]:
        return "Ready for practice"
    return "Validation required"


def show_previous_year_papers_page() -> None:
    apply_global_styles()
    st.title("NEET Previous Year Papers")
    st.caption("Only verified NEET papers are available in this student pilot. Every listed paper is linked to its original uploaded PDF and answer key.")

    papers = get_neet_papers()
    available_years = ["All", *[str(year) for year in sorted({paper["year"] for paper in papers}, reverse=True)]]
    selected_year = st.selectbox("Year", available_years)
    search_query = st.text_input("Search Papers", placeholder="Search by year or paper code").strip().lower()
    filtered = [
        paper
        for paper in papers
        if (selected_year == "All" or paper["year"] == int(selected_year))
        and (not search_query or search_query in f"{paper['year']} {paper['session']}".lower())
    ]

    st.dataframe(
        [
            {
                "Paper": paper["session"],
                "Questions": paper["questions"],
                "Scored Questions": paper["scored_questions"],
                "Duration": "3:20:00" if paper["duration_seconds"] == 12_000 else "3:00:00",
                "Format": paper["format_note"],
                "Status": paper_readiness(paper),
            }
            for paper in filtered
        ],
        width="stretch",
        hide_index=True,
    )

    for paper in filtered:
        st.divider()
        info_col, pdf_col, test_col = st.columns([2.5, 1, 1])
        info_col.subheader(paper["session"])
        info_col.caption(f"{paper['format_note']} | Maximum marks: {paper['max_marks']}")
        pdf_path = source_pdf_path(paper)
        if pdf_path.exists():
            pdf_col.download_button(
                "Download PDF",
                data=pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
                key=f"pdf_{paper['paper_id']}",
                width="stretch",
            )
        if test_col.button("Start Test", type="primary", key=f"start_{paper['paper_id']}", width="stretch"):
            st.session_state.pending_paper_id = paper["paper_id"]
            st.switch_page("pages/test_interface.py")


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Papers | ExamIQ AI", page_icon="📄", layout="wide")
    show_previous_year_papers_page()
