import csv
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


def chance_for_rank(predicted_rank: int, opening_rank: int, closing_rank: int) -> str:
    if predicted_rank <= opening_rank:
        return "Safe"
    if predicted_rank <= closing_rank:
        return "Moderate"
    if predicted_rank <= round(closing_rank * 1.2):
        return "Dream"
    return "Out of Range"


def clamp_marks(value: int | float) -> int:
    return max(0, min(720, int(value)))


def clamp_rank(value: int | float) -> int:
    return max(1, int(value))


def recommendations(rows: list[dict], category: str, state: str, predicted_rank: int) -> list[dict]:
    chance_order = {"Safe": 1, "Moderate": 2, "Dream": 3}
    recommended = []
    for row in rows:
        if row["Category"] != category or (state != "All India" and row["State"] != state):
            continue
        chance = chance_for_rank(predicted_rank, row["Opening Rank"], row["Closing Rank"])
        if chance != "Out of Range":
            recommended.append(
                {
                    "College": row["College"],
                    "State": row["State"],
                    "Institute Type": row["Institute Type"],
                    "Opening Rank": row["Opening Rank"],
                    "Closing Rank": row["Closing Rank"],
                    "Chance": chance,
                    "Source": row.get("Source", ""),
                }
            )
    return sorted(recommended, key=lambda row: (chance_order[row["Chance"]], row["Closing Rank"]))


def show_college_predictor_page() -> None:
    apply_global_styles()
    st.title("NEET College Explorer")
    st.caption("Explore the currently loaded NEET historical cutoff rows using your practice rank estimate.")
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
    default_marks = clamp_marks(st.session_state.get("prefill_marks", 620))
    default_rank = clamp_rank(st.session_state.get("prefill_air", 8000))
    default_category = student["category"] if student and student["category"] in categories else categories[0]
    default_state = student["state"] if student and student["state"] in states else "All India"

    input_1, input_2 = st.columns(2)
    with input_1:
        marks = st.number_input("NEET Practice Marks", min_value=0, max_value=720, value=default_marks, step=1)
        category = st.selectbox("Category", categories, index=categories.index(default_category))
    with input_2:
        predicted_rank = st.number_input("Practice Rank Estimate", min_value=1, value=default_rank, step=1)
        state = st.selectbox("Preferred State", states, index=states.index(default_state))

    if st.button("Explore Colleges", type="primary"):
        rows = recommendations(cutoffs, category, state, int(predicted_rank))
        if not rows:
            st.info("No matching rows are in the current NEET pilot dataset. Add verified cutoff records to expand coverage.")
        else:
            safe = sum(row["Chance"] == "Safe" for row in rows)
            moderate = sum(row["Chance"] == "Moderate" for row in rows)
            dream = sum(row["Chance"] == "Dream" for row in rows)
            metric_1, metric_2, metric_3 = st.columns(3)
            metric_1.metric("Safe", safe)
            metric_2.metric("Moderate", moderate)
            metric_3.metric("Dream", dream)
            st.dataframe(rows, width="stretch", hide_index=True)
        st.warning("Recommendations use historical cutoff rows only. Counselling rules, quotas, seats, category eligibility, and cutoffs change each year.")

    st.subheader("Loaded NEET Cutoff Records")
    st.dataframe(
        [
            {
                "College": row["College"],
                "Category": row["Category"],
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


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Colleges | ExamIQ AI", page_icon="🎓", layout="wide")
    show_college_predictor_page()
