"""
Helpers for the "Calendar Week" (CW) concept used across Preparation
(Safety Stock, E2E meetings, Training): format "YYYY-Wnn", ISO-8601 based.
"""
from __future__ import annotations

import datetime as dt
import re

CW_PATTERN = re.compile(r"^(\d{4})-W(\d{1,2})$")


def today_cw() -> str:
    iso = dt.date.today().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def date_to_cw(date: dt.date) -> str:
    iso = date.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def cw_to_monday(cw: str) -> dt.date | None:
    """Convert 'YYYY-Wnn' back to the Monday date of that ISO week."""
    match = CW_PATTERN.match(cw.strip()) if cw else None
    if not match:
        return None
    year, week = int(match.group(1)), int(match.group(2))
    try:
        return dt.date.fromisocalendar(year, week, 1)
    except ValueError:
        return None


def add_weeks_to_cw(cw: str, weeks: int) -> str:
    monday = cw_to_monday(cw)
    if monday is None:
        return ""
    new_date = monday + dt.timedelta(weeks=weeks)
    return date_to_cw(new_date)


def is_valid_cw(cw: str) -> bool:
    return bool(CW_PATTERN.match(cw.strip())) if cw else False
