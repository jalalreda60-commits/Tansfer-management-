"""
Global configuration for the Transfer Management System.

Centralises paths, enumerations and constants so every other module
(reads them from a single place instead of hard-coding strings.
"""
from __future__ import annotations

import os
import sys
from enum import Enum

APP_NAME = "Transfer Management System"
APP_ORG = "TMS"
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# When running from source, everything lives next to the project root.
# When frozen by PyInstaller (a distributed .exe), sys._MEIPASS is a
# temporary extraction folder that is wiped between runs, so persistent
# data (the SQLite DB, attachments, exports) must instead live in a
# writable, stable, per-user location next to the executable / in the
# OS app-data folder — otherwise every launch would start with an empty
# database.
if getattr(sys, "frozen", False):
    # Running as a PyInstaller-built executable.
    BASE_DIR = os.path.dirname(sys.executable)
    STYLES_DIR = os.path.join(getattr(sys, "_MEIPASS", BASE_DIR), "app", "resources", "styles")
    if not os.access(BASE_DIR, os.W_OK):
        # Fall back to a per-user app-data directory if installed to a
        # read-only location (e.g. "Program Files").
        appdata = os.getenv("APPDATA") or os.path.expanduser("~/.local/share")
        BASE_DIR = os.path.join(appdata, APP_NAME)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STYLES_DIR = os.path.join(BASE_DIR, "app", "resources", "styles")

DATA_DIR = os.path.join(BASE_DIR, "data")
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

for _dir in (DATA_DIR, ATTACHMENTS_DIR, EXPORTS_DIR):
    os.makedirs(_dir, exist_ok=True)

DATABASE_PATH = os.path.join(DATA_DIR, "transfer_management.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ---------------------------------------------------------------------------
# Enumerations (stored as plain strings in SQLite for simplicity/readability)
# ---------------------------------------------------------------------------


class TransferType(str, Enum):
    ONE_STEP = "1-Step"
    TWO_STEP = "2-Step"


class Activity(str, Enum):
    STAMPING = "Stamping"
    MOLDING = "Molding"


class SimpleStatus(str, Enum):
    """Not Started / Ongoing / Approved (PTT Internal)."""
    NOT_STARTED = "Not Started"
    ONGOING = "Ongoing"
    APPROVED = "Approved"


class OEMStatus(str, Enum):
    NOT_STARTED = "Not Started"
    ONGOING = "Ongoing"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class NAOngoingDone(str, Enum):
    NA = "NA"
    ONGOING = "Ongoing"
    DONE = "Done"


class NAOngoingReceived(str, Enum):
    NA = "NA"
    ONGOING = "Ongoing"
    RECEIVED = "Received"


class PrecheckFeedback(str, Enum):
    NA = "NA"
    ONGOING = "Ongoing"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


class YesNo(str, Enum):
    YES = "Yes"
    NO = "No"


class PCNStatus(str, Enum):
    NOT_SENT = "Not Sent"
    SENT = "Sent"
    ONGOING = "Ongoing"
    APPROVED = "Approved"


class TrainingStatus(str, Enum):
    NOT_STARTED = "Not Started"
    ONGOING = "Ongoing"
    DONE = "Done"


class MeetingStatus(str, Enum):
    NOT_SCHEDULED = "Not Scheduled"
    SCHEDULED = "Scheduled"
    DONE = "Done"


class Urgency(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class OverallStatus(str, Enum):
    """Used for computed / rolled-up statuses across the app."""
    NOT_STARTED = "Not Started"
    ONGOING = "Ongoing"
    DELAYED = "Delayed"
    COMPLETED = "Completed"


# Colour palette used consistently for OverallStatus everywhere (tables,
# KPI cards, charts, badges).
STATUS_COLORS = {
    OverallStatus.COMPLETED.value: "#2ecc71",   # green
    OverallStatus.ONGOING.value: "#f1c40f",     # yellow
    OverallStatus.DELAYED.value: "#e74c3c",     # red
    OverallStatus.NOT_STARTED.value: "#95a5a6",  # grey
}

SIDEBAR_MODULES = ["Dashboard", "Transfers", "Preparation", "Release"]

TECHNOLOGIES = ["Injection Molding", "Progressive Stamping", "Transfer Molding",
                 "Deep Draw Stamping", "Insert Molding", "Other"]

LOCATIONS = ["Plant A - Germany", "Plant B - Poland", "Plant C - Mexico",
             "Plant D - China", "Plant E - Morocco", "Other"]
