import os

import streamlit as st

from database import initialize_database
from student_store import current_student
from ui_theme import apply_global_styles


def main() -> None:
    st.set_page_config(
        page_title="ExamIQ AI | NEET",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    initialize_database()
    apply_global_styles()

    student = current_student(st.session_state)
    st.sidebar.title("ExamIQ AI")
    st.sidebar.caption("NEET Practice")
    if student:
        st.sidebar.caption(f"Signed in as {student['name']}")
    else:
        st.sidebar.caption("Student sign-in")

    if student:
        nav_col_1, nav_col_2 = st.sidebar.columns(2)
        if nav_col_1.button("Home", width="stretch"):
            st.switch_page("pages/dashboard.py")
        if nav_col_2.button("Logout", width="stretch"):
            st.session_state.pop("current_student", None)
            st.session_state.active_attempt_id = None
            st.session_state.pop("active_challenge_id", None)
            st.switch_page("pages/login.py")

    pages = {
        "👨‍🎓 Student": [
            st.Page("pages/login.py", title="Login", icon="🔐"),
            st.Page("pages/register.py", title="Register", icon="📝"),
        ],
        "🧾 System": [
            st.Page("pages/about_examiq.py", title="About ExamIQ AI", icon="ℹ️"),
        ],
    }

    if student:
        pages = {
            "🏠 Dashboard": [
                st.Page("pages/dashboard.py", title="Dashboard", icon="🏠"),
            ],
            **pages,
            "📚 Examination": [
                st.Page("pages/previous_year_papers.py", title="Previous Papers", icon="📄"),
                st.Page("pages/test_interface.py", title="NEET Practice Test", icon="🧪"),
            ],
            "🤝 Competition": [
                st.Page("pages/head_to_head.py", title="Head-to-Head", icon="🏁"),
            ],
            "📊 Results": [
                st.Page("pages/result_dashboard.py", title="Result Dashboard", icon="📊"),
                st.Page("pages/performance_analytics.py", title="Performance Analytics", icon="📈"),
            ],
            "🏆 Prediction": [
                st.Page("pages/rank_predictor.py", title="Rank Predictor", icon="🏆"),
                st.Page("pages/college_predictor.py", title="College Predictor", icon="🎓"),
            ],
        }
        pages["👨‍🎓 Student"].extend(
            [
                st.Page("pages/student_profile.py", title="Student Profile", icon="👤"),
                st.Page("pages/student_history.py", title="Student History", icon="📚"),
                st.Page("pages/feedback.py", title="Feedback", icon="⭐"),
            ]
        )

    admin_email = os.getenv("EXAMIQ_ADMIN_EMAIL", "").strip().lower()
    if student and admin_email and student["email"].lower() == admin_email:
        pages["⚙ Administration"] = [
            st.Page("pages/admin_panel.py", title="Admin Panel", icon="⚙"),
            st.Page("pages/system_status.py", title="System Status", icon="🟢"),
        ]

    navigation = st.navigation(pages)
    redirect_after_login = st.session_state.pop("redirect_after_login", None)
    if redirect_after_login:
        st.switch_page(redirect_after_login)
    navigation.run()


if __name__ == "__main__":
    main()
