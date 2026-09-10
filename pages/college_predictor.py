from __future__ import annotations

import csv
import re
from pathlib import Path

import streamlit as st

from student_store import current_student
from ui_theme import apply_global_styles


BASE_DIR = Path(__file__).resolve().parents[1]
CUTOFF_DATA_PATH = BASE_DIR / "datasets" / "college_cutoffs" / "college_cutoffs.csv"


def load_cutoff_data() -> list[dict]:
    with CUTOFF_DATA_PATH.open("r", encoding="utf-8") as cutoff_file:
        return [
            {**row, "Opening Rank": int(row["Opening Rank"]), "Closing Rank": int(row["Closing Rank"])}
            for row in csv.DictReader(cutoff_file)
            if row["Exam"] == "NEET"
        ]


def counselling_year(row: dict) -> str:
    match = re.search(r"\b20\d{2}\b", row.get("Notes", ""))
    return match.group(0) if match else "Not stated"


def fit_band(predicted_rank: int, closing_rank: int) -> str:
    """Group historical cutoff alignment without presenting it as an admission promise."""
    if predicted_rank <= round(closing_rank * 0.7):
        return "Safer"
    if predicted_rank <= closing_rank:
        return "Target"
    if predicted_rank <= round(closing_rank * 1.1):
        return "Aspirational"
    return "Outside range"


def clamp_marks(value: int | float | None) -> int:
    return max(0, min(720, int(value or 0)))


def clamp_rank(value: int | float | None) -> int:
    return max(1, int(value or 1))


def recommendations(rows: list[dict], category: str, state: str, predicted_rank: int) -> list[dict]:
    band_order = {"Safer": 1, "Target": 2, "Aspirational": 3}
    recommended = []
    for row in rows:
        if row["Category"] != category or (state != "All India" and row["State"] != state):
            continue
        band = fit_band(predicted_rank, row["Closing Rank"])
        if band == "Outside range":
            continue
        recommended.append(
            {
                "College": row["College"],
                "State": row["State"],
                "Institute Type": row["Institute Type"],
                "Counselling Year": counselling_year(row),
                "Opening Rank": row["Opening Rank"],
                "Closing Rank": row["Closing Rank"],
                "Historical Fit": band,
                "Source URL": row.get("Source URL", ""),
            }
        )
    return sorted(recommended, key=lambda row: (band_order[row["Historical Fit"]], row["Closing Rank"]))


def show_college_predictor_page() -> None:
    apply_global_styles()
    st.title("NEET College Explorer")
    st.caption("Compare your practice rank with sourced historical counselling cutoff records.")
    if not CUTOFF_DATA_PATH.exists():
        st.error("College cutoff data is missing. Expected: datasets/college_cutoffs/college_cutoffs.csv")
        return

    cutoffs = load_cutoff_data()
    if not cutoffs:
        st.warning("No NEET cutoff rows are currently loaded.")
        return

    student = current_student(st.session_state)
    categories = sorted({row["Category"] for row in cutoffs})
    states = ["All India"] + sorted({row["State"] for row in cutoffs})
    saved_marks = st.session_state.get("prefill_marks")
    saved_rank = st.session_state.get("prefill_air")
    default_marks = clamp_marks(saved_marks)
    default_rank = clamp_rank(saved_rank)
    default_category = student["category"] if student and student["category"] in categories else categories[0]
    default_state = student["state"] if student and student["state"] in states else "All India"

    coverage_1, coverage_2, coverage_3 = st.columns(3)
    coverage_1.metric("Sourced NEET records", len(cutoffs))
    coverage_2.metric("States represented", len({row["State"] for row in cutoffs}))
    coverage_3.metric("Categories represented", len(categories))

    with st.form("college_explorer_form"):
        input_1, input_2 = st.columns(2)
        with input_1:
            marks = st.number_input(
                "NEET practice marks",
                min_value=0,
                max_value=720,
                value=default_marks,
                step=1,
            )
            category = st.selectbox("Counselling category", categories, index=categories.index(default_category))
        with input_2:
            predicted_rank = st.number_input(
                "Practice rank estimate",
                min_value=1,
                value=default_rank,
                step=1,
            )
            state = st.selectbox("Preferred state", states, index=states.index(default_state))
        explore = st.form_submit_button("Explore historical cutoffs", type="primary")

    if explore:
        rows = recommendations(cutoffs, category, state, int(predicted_rank))
        st.session_state.college_explorer_rows = rows
        st.session_state.college_explorer_rank = int(predicted_rank)
        st.session_state.college_explorer_marks = int(marks)

    rows = st.session_state.get("college_explorer_rows")
    if rows is not None:
        st.subheader("Historical Fit")
        if not rows:
            st.info("No loaded cutoff record aligns with these filters. This is not a statement about your admission chances.")
        else:
            safer = sum(row["Historical Fit"] == "Safer" for row in rows)
            target = sum(row["Historical Fit"] == "Target" for row in rows)
            aspirational = sum(row["Historical Fit"] == "Aspirational" for row in rows)
            metric_1, metric_2, metric_3 = st.columns(3)
            metric_1.metric("Safer historical fit", safer)
            metric_2.metric("Target historical fit", target)
            metric_3.metric("Aspirational", aspirational)
            st.dataframe(
                [{key: value for key, value in row.items() if key != "Source URL"} for row in rows],
                width="stretch",
                hide_index=True,
            )
            source_urls = sorted({row["Source URL"] for row in rows if row["Source URL"]})
            if source_urls:
                st.link_button("Open source for displayed cutoff data", source_urls[0], width="stretch")

    st.subheader("Data Coverage")
    st.dataframe(
        [
            {
                "College": row["College"],
                "Category": row["Category"],
                "Counselling Year": counselling_year(row),
                "Opening Rank": row["Opening Rank"],
                "Closing Rank": row["Closing Rank"],
                "State": row["State"],
                "Institute Type": row["Institute Type"],
            }
            for row in cutoffs
        ],
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Historical records are planning inputs only. Counselling eligibility, quota, seats, round, domicile rules, "
        "and cutoffs can change. Always confirm choices from the official counselling authority."
    )


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Colleges | ExamIQ AI", page_icon="🎓", layout="wide")
    show_college_predictor_page()
