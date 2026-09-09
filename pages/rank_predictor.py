import csv
from pathlib import Path

import streamlit as st

from ui_theme import apply_global_styles


BASE_DIR = Path(__file__).resolve().parents[1]
RANK_DATA_PATH = BASE_DIR / "datasets" / "neet_rank_data.csv"


def load_rank_data() -> list[dict]:
    with RANK_DATA_PATH.open("r", encoding="utf-8") as rank_file:
        reader = csv.DictReader(rank_file)
        rows = [{"marks": int(row["Marks"]), "air": int(row["AIR"])} for row in reader]

    return sorted(rows, key=lambda row: row["marks"], reverse=True)


def predict_air(marks: int, rank_data: list[dict]) -> int:
    if marks >= rank_data[0]["marks"]:
        return rank_data[0]["air"]

    if marks <= rank_data[-1]["marks"]:
        return rank_data[-1]["air"]

    for high, low in zip(rank_data, rank_data[1:]):
        if high["marks"] >= marks >= low["marks"]:
            marks_range = high["marks"] - low["marks"]
            rank_range = low["air"] - high["air"]
            marks_drop = high["marks"] - marks
            predicted_rank = high["air"] + ((marks_drop / marks_range) * rank_range)
            return round(predicted_rank)

    return rank_data[-1]["air"]


def performance_category(marks: int) -> str:
    if marks >= 650:
        return "Excellent"
    if marks >= 600:
        return "Very Good"
    if marks >= 550:
        return "Good"
    if marks >= 500:
        return "Average"
    return "Needs Improvement"


def competition_level(predicted_air: int) -> str:
    if predicted_air <= 1000:
        return "Top national competition zone"
    if predicted_air <= 10000:
        return "Highly competitive zone"
    if predicted_air <= 50000:
        return "Moderate competition zone"
    return "High improvement required zone"


def better_than_percent(predicted_air: int, rank_data: list[dict]) -> float:
    estimated_students = rank_data[-1]["air"]
    percentile = (1 - (predicted_air / estimated_students)) * 100
    return round(max(0, min(99.9, percentile)), 1)


def clamp_marks(value: int | float) -> int:
    return max(0, min(720, int(value)))


def show_rank_predictor_page() -> None:
    apply_global_styles()
    st.title("NEET Rank Estimate")
    st.caption("Practice estimate using the currently loaded NEET marks-to-AIR reference dataset.")

    if not RANK_DATA_PATH.exists():
        st.error("Rank dataset missing. Expected: datasets/neet_rank_data.csv")
        return

    rank_data = load_rank_data()
    default_marks = clamp_marks(st.session_state.get("prefill_marks", 620))

    if "latest_result" in st.session_state:
        st.success("Loaded marks from the latest Result Dashboard calculation.")

    marks = st.number_input("Enter Marks", min_value=0, max_value=720, value=default_marks, step=1)

    show_prediction = st.button("Predict Rank", type="primary") or "prefill_marks" in st.session_state
    if show_prediction:
        predicted_air = predict_air(int(marks), rank_data)
        category = performance_category(int(marks))
        percentile = better_than_percent(predicted_air, rank_data)
        level = competition_level(predicted_air)
        st.session_state.prefill_air = predicted_air
        st.session_state.prefill_marks = int(marks)

        st.subheader("Practice Estimate")
        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric("Predicted AIR", f"{predicted_air:,}")
        metric_2.metric("Performance Category", category)
        metric_3.metric("Better Than", f"{percentile}%")

        st.info(f"Expected Competition Level: {level}")
        st.warning("This is a planning estimate from a limited reference dataset. It is not an NTA result, AIR guarantee, or counselling prediction.")
        next_col_1, next_col_2 = st.columns(2)
        if next_col_1.button("Predict Colleges", type="primary", width="stretch"):
            st.switch_page("pages/college_predictor.py")
        if next_col_2.button("Give Feedback", width="stretch"):
            st.switch_page("pages/feedback.py")

    st.subheader("Loaded Reference Points")
    st.dataframe(
        [{"Marks": row["marks"], "AIR": row["air"]} for row in rank_data],
        width="stretch",
        hide_index=True,
    )


if __name__ == "__main__":
    st.set_page_config(page_title="Rank Predictor | ExamIQ AI", page_icon="🏆", layout="centered")
    show_rank_predictor_page()
