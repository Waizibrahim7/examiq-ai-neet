from __future__ import annotations

import re

import streamlit as st

from database import storage_status
from india_data import CATEGORIES, INDIA_STATES_AND_UTS
from otp_auth import email_otp_enabled, send_email_otp, verify_email_otp
from student_store import register_student
from ui_theme import apply_global_styles


def registration_is_valid(details: dict, password: str, confirm_password: str) -> str | None:
    if not all([*details.values(), password, confirm_password]):
        return "Please complete every required field."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", details["email"]):
        return "Enter a valid email address."
    if not details["mobile"].isdigit() or len(details["mobile"]) != 10:
        return "Enter a valid 10-digit mobile number."
    if password != confirm_password:
        return "Password and confirmation do not match."
    if len(password) < 8:
        return "Use a password with at least 8 characters."
    return None


def finish_registration(details: dict, password: str) -> None:
    student = register_student(details, password)
    st.session_state.current_student = student
    st.session_state.pop("pending_registration", None)
    st.session_state.redirect_after_login = "pages/dashboard.py"
    st.rerun()


def render_email_verification() -> None:
    pending = st.session_state.get("pending_registration")
    if not pending:
        return

    st.divider()
    st.subheader("Verify your email")
    st.caption(f"A six-digit verification code was sent to {pending['details']['email']}.")
    with st.form("email_otp_form"):
        token = st.text_input("Verification code", max_chars=6, placeholder="123456")
        verify_clicked = st.form_submit_button("Verify email and create account", type="primary")

    resend_col, cancel_col = st.columns(2)
    if resend_col.button("Resend code", width="stretch"):
        try:
            send_email_otp(pending["details"]["email"], allow_signup=True)
            st.success("A new verification code has been sent.")
        except ValueError as error:
            st.error(str(error))
    if cancel_col.button("Cancel registration", width="stretch"):
        st.session_state.pop("pending_registration", None)
        st.rerun()

    if verify_clicked:
        if not verify_email_otp(pending["details"]["email"], token):
            st.error("That verification code is not valid. Request a new code and try again.")
            return
        try:
            finish_registration(pending["details"], pending["password"])
        except ValueError as error:
            st.error(str(error))


def show_register_page() -> None:
    apply_global_styles()
    st.header("Create Student Account")
    st.caption("Create one account to save NEET attempts, results, and college-planning preferences.")

    storage = storage_status()
    if storage["persistent"]:
        st.success(str(storage["detail"]))
    else:
        st.warning(f"{storage['detail']} Do not reuse a password from any other service.")

    with st.form("registration_form"):
        full_name = st.text_input("Full name", placeholder="Enter your full name", autocomplete="name")
        email = st.text_input("Email address", placeholder="student@example.com", autocomplete="email")
        mobile_number = st.text_input("Mobile number", placeholder="10-digit mobile number", autocomplete="tel")
        password = st.text_input("Password", type="password", placeholder="Create a password", autocomplete="new-password")
        confirm_password = st.text_input(
            "Confirm password", type="password", placeholder="Re-enter password", autocomplete="new-password"
        )
        st.text_input("Exam", value="NEET", disabled=True)
        category = st.selectbox("Counselling category", CATEGORIES)
        state = st.selectbox(
            "State / Union Territory",
            INDIA_STATES_AND_UTS,
            index=None,
            placeholder="Select your state or union territory",
        )
        submit_label = "Send verification code" if email_otp_enabled() else "Create account"
        register_clicked = st.form_submit_button(submit_label, type="primary")

    if register_clicked:
        details = {
            "name": full_name,
            "email": email.strip().lower(),
            "mobile": mobile_number,
            "category": category,
            "state": state,
        }
        error = registration_is_valid(details, password, confirm_password)
        if error:
            st.error(error)
            return

        if email_otp_enabled():
            try:
                send_email_otp(details["email"], allow_signup=True)
                st.session_state.pending_registration = {"details": details, "password": password}
                st.rerun()
            except ValueError as otp_error:
                st.error(str(otp_error))
            return

        try:
            finish_registration(details, password)
        except ValueError as registration_error:
            st.error(str(registration_error))

    if email_otp_enabled():
        render_email_verification()
    else:
        st.caption("Email verification will be available when ExamIQ's verified email service is configured.")


if __name__ == "__main__":
    st.set_page_config(page_title="Register | ExamIQ AI", page_icon="📘", layout="centered")
    show_register_page()
