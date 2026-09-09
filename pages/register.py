import streamlit as st

from student_store import register_student
from ui_theme import apply_global_styles


def show_register_page() -> None:
    apply_global_styles()
    st.header("Create Student Account")
    st.caption("Register once to start taking tests and tracking your exam readiness.")

    with st.form("registration_form"):
        full_name = st.text_input("Full Name", placeholder="Enter your full name")
        email = st.text_input("Email", placeholder="student@example.com")
        mobile_number = st.text_input("Mobile Number", placeholder="10-digit mobile number")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
        st.text_input("Exam", value="NEET", disabled=True)
        category = st.selectbox("Category", ["General", "OBC", "SC", "ST", "EWS"])
        state = st.text_input("State", placeholder="Example: Uttar Pradesh")
        register_clicked = st.form_submit_button("Register Now")

    if register_clicked:
        if not all([full_name, email, mobile_number, password, confirm_password, category, state]):
            st.warning("Please complete all fields.")
        elif "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            st.error("Enter a valid email address.")
        elif not mobile_number.isdigit() or len(mobile_number) != 10:
            st.error("Enter a valid 10-digit mobile number.")
        elif password != confirm_password:
            st.error("Password and Confirm Password do not match.")
        else:
            try:
                student = register_student(
                    {
                        "name": full_name,
                        "email": email,
                        "mobile": mobile_number,
                        "category": category,
                        "state": state,
                    },
                    password,
                )
            except ValueError as error:
                st.error(str(error))
                return
            st.session_state.current_student = student
            st.session_state.redirect_after_login = "pages/dashboard.py"
            st.rerun()


if __name__ == "__main__":
    st.set_page_config(page_title="Register | ExamIQ AI", page_icon="📘", layout="centered")
    show_register_page()
