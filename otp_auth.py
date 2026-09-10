"""Optional Supabase email OTP integration for verified student registrations."""

from __future__ import annotations

from deployment_config import email_otp_configured, setting


def email_otp_enabled() -> bool:
    return email_otp_configured()


def _client():
    if not email_otp_enabled():
        raise ValueError("Email verification is not configured for this deployment.")

    try:
        from supabase import create_client
    except ImportError as error:
        raise ValueError("The OTP client is not installed on this deployment.") from error

    return create_client(setting("SUPABASE_URL"), setting("SUPABASE_PUBLISHABLE_KEY"))


def send_email_otp(email: str, allow_signup: bool) -> None:
    try:
        _client().auth.sign_in_with_otp(
            {
                "email": email.strip().lower(),
                "options": {"should_create_user": allow_signup},
            }
        )
    except Exception as error:
        raise ValueError("We could not send a verification code. Please wait and try again.") from error


def verify_email_otp(email: str, token: str) -> bool:
    if not token.isdigit() or len(token) != 6:
        return False

    try:
        response = _client().auth.verify_otp(
            {
                "email": email.strip().lower(),
                "token": token,
                "type": "email",
            }
        )
        return bool(getattr(response, "user", None))
    except Exception:
        return False
