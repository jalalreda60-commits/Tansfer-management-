"""
Small, dependency-free validation helpers used by dialogs before saving.
Return (is_valid, error_message).
"""
from __future__ import annotations


def require_non_empty(value: str, field_label: str):
    if value is None or not str(value).strip():
        return False, f"'{field_label}' is required."
    return True, ""


def require_unique(value: str, existing_values: list[str], field_label: str, current=None):
    normalized = [v.strip().lower() for v in existing_values if v is not None]
    if current is not None:
        try:
            normalized.remove(current.strip().lower())
        except ValueError:
            pass
    if value.strip().lower() in normalized:
        return False, f"'{field_label}' must be unique. '{value}' already exists."
    return True, ""


def validate_all(*checks):
    """checks is a list of (is_valid, message) tuples; returns first failure or (True, '')."""
    for is_valid, message in checks:
        if not is_valid:
            return False, message
    return True, ""
