from __future__ import annotations

import streamlit as st

from database import (
    create_challenge,
    get_challenge_attempts,
    get_student_challenges,
    join_challenge,
    storage_status,
)
from neet_catalog import get_neet_paper, get_neet_papers
from result_engine import calculate_result, load_answer_key
from student_store import current_student
from ui_theme import apply_global_styles


def paper_label(paper: dict) -> str:
    return f"{paper['session']} ({paper['questions']} questions)"


def available_papers() -> list[dict]:
    """Only offer papers with an answer key that can produce a real result."""
    return [paper for paper in get_neet_papers() if len(load_answer_key(paper["paper_id"])) == paper["questions"]]


def result_rows(challenge_id: str, student: dict) -> list[dict]:
    rows = []
    for index, attempt in enumerate(get_challenge_attempts(challenge_id), start=1):
        label = "You" if attempt["student_email"] == student["email"] else f"Opponent {index}"
        row = {"Student": label, "Status": "Not submitted", "Score": "--", "Accuracy": "--"}
        if attempt.get("submitted"):
            answer_key = load_answer_key(attempt["paper_id"])
            result = calculate_result(attempt["answers"], answer_key, attempt["paper_id"])
            row.update(
                {
                    "Status": "Submitted",
                    "Score": f"{result['score']}/{result['max_score']}",
                    "Accuracy": f"{result['accuracy']:.1f}%",
                    "sort_score": result["score"],
                    "sort_accuracy": result["accuracy"],
                }
            )
        rows.append(row)
    return sorted(rows, key=lambda row: (row.get("sort_score", -1), row.get("sort_accuracy", -1)), reverse=True)


def open_challenge(challenge: dict, student: dict) -> None:
    paper = get_neet_paper(challenge["paper_id"])
    if not paper:
        st.error("This challenge refers to a paper that is no longer available.")
        return

    st.subheader(paper["session"])
    status = "Waiting for an opponent" if challenge["member_count"] == 1 else "Opponent joined"
    first, second, third = st.columns(3)
    first.metric("Room", challenge["share_code"])
    second.metric("Participants", f"{challenge['member_count']} / 2")
    third.metric("Room status", status)
    st.caption(
        "Each student receives the official paper duration from their own start time. "
        "Names and contact details are not shown to opponents."
    )

    if challenge["member_count"] == 2:
        if st.button("Start My Challenge Test", type="primary", width="stretch"):
            st.session_state.pending_paper_id = paper["paper_id"]
            st.session_state.active_challenge_id = challenge["challenge_id"]
            st.switch_page("pages/test_interface.py")
    else:
        st.info("Share the room code with one student. Testing unlocks when they join.")

    rows = result_rows(challenge["challenge_id"], student)
    st.subheader("Challenge Results")
    st.dataframe([{key: value for key, value in row.items() if not key.startswith("sort_")} for row in rows], hide_index=True, width="stretch")
    submitted = [row for row in rows if row["Status"] == "Submitted"]
    if len(submitted) == 2:
        if submitted[0]["sort_score"] == submitted[1]["sort_score"]:
            st.info("The challenge is level on marks. Accuracy is used as the visible tie-breaker.")
        elif submitted[0]["Student"] == "You":
            st.success("You lead this completed challenge on score.")
        else:
            st.info("Your opponent currently leads on score.")


def show_head_to_head_page() -> None:
    apply_global_styles()
    st.title("NEET Head-to-Head")
    st.caption("Take the same verified NEET paper with one other student and compare only real submitted results.")
    student = current_student(st.session_state)
    if not student:
        st.warning("Sign in to create or join a private challenge.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/login.py")
        return

    storage = storage_status()
    if not storage["persistent"]:
        st.warning(
            "Head-to-head rooms are unavailable on the local pilot database. "
            "They will be enabled after managed cloud storage is connected, so shared results do not disappear on restart."
        )
        return

    papers = available_papers()
    papers_by_id = {paper["paper_id"]: paper for paper in papers}
    create_col, join_col = st.columns(2)
    with create_col:
        st.subheader("Create a private room")
        with st.form("create_challenge"):
            selected_id = st.selectbox(
                "Verified NEET paper",
                list(papers_by_id),
                format_func=lambda paper_id: paper_label(papers_by_id[paper_id]),
            )
            create_room = st.form_submit_button("Create Challenge", type="primary", width="stretch")
        if create_room:
            room = create_challenge(student["email"], selected_id)
            st.session_state.active_challenge_id = room["challenge_id"]
            st.rerun()

    with join_col:
        st.subheader("Join a private room")
        with st.form("join_challenge"):
            share_code = st.text_input("Room code", placeholder="NEET-ABC123").strip().upper()
            join_room = st.form_submit_button("Join Challenge", width="stretch")
        if join_room:
            if not share_code:
                st.error("Enter the room code shared by the other student.")
            else:
                try:
                    room = join_challenge(share_code, student["email"])
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.session_state.active_challenge_id = room["challenge_id"]
                    st.rerun()

    challenges = get_student_challenges(student["email"])
    if not challenges:
        st.info("Create a room or join one with a code to begin a private NEET challenge.")
        return

    challenge_ids = [challenge["challenge_id"] for challenge in challenges]
    selected_id = st.session_state.get("active_challenge_id")
    if selected_id not in challenge_ids:
        selected_id = challenge_ids[0]
    selected = st.selectbox(
        "Your challenge rooms",
        challenge_ids,
        index=challenge_ids.index(selected_id),
        format_func=lambda challenge_id: next(
            f"{challenge['share_code']} - {get_neet_paper(challenge['paper_id'])['year']}"
            for challenge in challenges
            if challenge["challenge_id"] == challenge_id
        ),
    )
    st.session_state.active_challenge_id = selected
    active_challenge = next(challenge for challenge in challenges if challenge["challenge_id"] == selected)
    open_challenge(active_challenge, student)


if __name__ == "__main__":
    st.set_page_config(page_title="NEET Head-to-Head | ExamIQ AI", page_icon="🏁", layout="wide")
    show_head_to_head_page()
