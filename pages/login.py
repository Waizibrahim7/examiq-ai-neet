import streamlit as st

from neet_catalog import get_neet_papers
from student_store import authenticate_student
from ui_theme import apply_global_styles


def apply_login_styles() -> None:
    st.markdown(
        """
        <style>
            .login-brand {
                min-height: 390px;
                padding: 2.4rem 2.2rem;
                border: 1px solid #0d5f50;
                border-left: 5px solid #36a98c;
                background: #123d2c;
                border-radius: 6px;
            }
            .login-brand h1 {
                margin: 1.2rem 0 0.65rem;
                font-size: 2.35rem;
                line-height: 1.12;
                color: #ffffff !important;
            }
            .login-brand p { color: #e5f4ea !important; }
            .login-kicker {
                color: #9ee0c6 !important;
                font-size: 0.86rem;
                font-weight: 800;
                text-transform: uppercase;
            }
            .login-mark {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 48px;
                height: 48px;
                border: 1px solid #8bcbb2;
                border-radius: 6px;
                background: #0c6d5d;
                color: #ffffff;
                font-size: 1.35rem;
                font-weight: 800;
            }
            div[data-testid="stForm"] {
                border: 1px solid #c9d9ce;
                border-radius: 6px;
                background: #ffffff;
                padding: 1.35rem 1.35rem 0.6rem;
            }
            div[data-testid="stFormSubmitButton"] button {
                width: 100%;
                min-height: 2.7rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_login_page() -> None:
    apply_global_styles()
    apply_login_styles()
    brand_col, form_col = st.columns([1.05, 0.95], gap="large")

    with brand_col:
        paper_count = len(get_neet_papers())
        st.markdown(
            f"""
            <section class="login-brand">
                <div class="login-mark">E</div>
                <p class="login-kicker">ExamIQ AI</p>
                <h1>Your NEET practice, in one place.</h1>
                <p>Continue with your own papers, saved attempts, and performance record.</p>
                <br>
                <p><strong>{paper_count} verified NEET papers</strong></p>
                <p><strong>Personal test history</strong></p>
                <p><strong>Practice results</strong></p>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with form_col:
        st.subheader("Welcome back")
        st.caption("Sign in to your student account.")
        with st.form("login_form"):
            email = st.text_input("Email address", placeholder="name@example.com", autocomplete="email")
            password = st.text_input("Password", type="password", placeholder="Enter your password", autocomplete="current-password")
            login_clicked = st.form_submit_button("Sign in", type="primary")

        st.caption("Passwords are stored as secure hashes. Never share your account credentials.")
        action_col, support_col = st.columns(2)
        with action_col:
            if st.button("Create account", width="stretch"):
                st.switch_page("pages/register.py")
        with support_col:
            st.link_button("Contact support", "mailto:support@examiq.ai", width="stretch")

    if login_clicked:
        if not email or not password:
            st.warning("Enter your email address and password.")
            return
        student = authenticate_student(email, password)
        if not student:
            st.error("We could not sign you in. Check your email address and password.")
            return

        st.session_state.current_student = student
        st.session_state.redirect_after_login = "pages/dashboard.py"
        st.rerun()


if __name__ == "__main__":
    st.set_page_config(page_title="Login | ExamIQ AI", page_icon="📘", layout="centered")
    show_login_page()
