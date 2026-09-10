"""Deployment capability checks used to keep student-facing security claims honest."""

from __future__ import annotations

import os


def setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        import streamlit as st

        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def managed_storage_configured() -> bool:
    return setting("EXAMIQ_DATABASE_URL").startswith(("postgres://", "postgresql://"))


def email_otp_configured() -> bool:
    return bool(setting("SUPABASE_URL") and setting("SUPABASE_PUBLISHABLE_KEY"))


def phone_otp_configured() -> bool:
    return email_otp_configured() and bool(setting("SUPABASE_PHONE_OTP_ENABLED"))


def storage_label() -> str:
    return "Managed PostgreSQL" if managed_storage_configured() else "Local SQLite pilot"
