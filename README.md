# Transfer Management System

A production-ready desktop application for managing manufacturing transfer
projects from **Preparation** through **Release**, built with Python,
PySide6 and SQLAlchemy.

## Features

- **Dashboard** — KPI cards, progress/distribution charts, recent
  activity, upcoming due dates and delayed-task tables, with a live
  Green / Yellow / Red / Grey status system.
- **Transfers** — full CRUD, duplication, search, filters, sorting,
  Excel export, printing, file attachments, comments and a full history
  log, with a nested Tools → Part Numbers editor.
- **Preparation** — PTT Approval (internal + multi-OEM), Safety Stock
  Build-up, Raw Material Follow-up, Pre-check, E2E Follow-up (Kick-off /
  PCN & PPAP / SOP Readiness), Applicator or Counter Part check
  (conditional on Activity), and Training — each with automatic
  progress/status roll-ups.
- **Release** — a configurable release checklist per transfer with
  automatic progress and a "Finalize Release" action.
- Dark / Light theme toggle, collapsible sidebar, automatic saving
  (every field commits to SQLite immediately), calendar-week (ISO
  `YYYY-Wnn`) support, and a background Notification Center that flags
  overdue activities and upcoming transfer dates.

## Technology Stack

- Python 3.13
- PySide6 (UI + QtCharts + QtPrintSupport)
- SQLAlchemy ORM over SQLite
- openpyxl for Excel export

## Project Structure

```
transfer_management_system/
├── main.py                     # Entry point
├── requirements.txt
├── build.spec                   # PyInstaller spec -> Windows .exe
├── .github/workflows/
│   └── build-exe.yml             # CI: builds & publishes the .exe
├── .gitignore
├── app/
│   ├── config.py                # Paths, enums, constants, colour palette
│   ├── database.py               # SQLAlchemy engine/session bootstrap
│   ├── models/                   # One module per entity (see below)
│   ├── controllers/               # Business logic / persistence (MVC "C")
│   │   ├── transfer_controller.py
│   │   ├── preparation_controller.py
│   │   ├── release_controller.py
│   │   ├── dashboard_controller.py
│   │   └── notification_controller.py
│   ├── views/                     # PySide6 UI (MVC "V")
│   │   ├── main_window.py, sidebar.py
│   │   ├── dashboard_view.py, transfers_view.py,
│   │   │   preparation_view.py, release_view.py
│   │   ├── widgets/                # Reusable UI components
│   │   │   ├── kpi_card.py, status_badge.py, progress_widget.py,
│   │   │   │   charts.py, dynamic_form.py
│   │   └── dialogs/
│   │       ├── transfer_dialog.py, entity_detail_dialog.py,
│   │       │   notification_center_dialog.py
│   ├── utils/                      # calendar_week, excel_export, theme, validators
│   └── resources/styles/
├── data/                            # transfer_management.db (SQLite, created on first run)
├── attachments/                     # Copied file attachments
└── exports/                         # Generated .xlsx exports
```

### Database schema (SQLAlchemy models)

```
Transfer 1───* Tool 1───* PartNumber
Transfer 1───1 PTTApproval 1───* OEMApproval
Transfer 1───1 E2EFollowUp
Transfer 1───1 ReleaseChecklist 1───* ReleaseItem
Tool     1───1 SafetyStock
Tool     1───1 Training
PartNumber 1───1 RawMaterial
PartNumber 1───1 PreCheck
PartNumber 1───1 Applicator      (Activity = Stamping)
PartNumber 1───1 CounterPart     (Activity = Molding)

Attachment / Comment / HistoryLog / Notification are polymorphic
(entity_type + entity_id) and attach to any of the above.
```

### Why a `DynamicForm` widget?

Sections 3.1–3.7 of the spec define seven visually-similar but
field-different sub-forms. Rather than hand-rolling seven near-identical
`QFormLayout` blocks, `app/views/widgets/dynamic_form.py` builds a form
from a declarative field list (`{"attr", "label", "type", "options"}`)
and binds it to any SQLAlchemy object, auto-saving on every edit. Each
Preparation tab is therefore ~20 lines of field spec instead of ~150
lines of boilerplate.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The SQLite database is created automatically on first launch at
`data/transfer_management.db` — no manual migration step needed.

## Building the Windows .exe

The project ships with a PyInstaller spec (`build.spec`) that produces a
single-file `TransferManagementSystem.exe` with no Python installation
required on the target machine.

### Locally (on Windows)

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build.spec --noconfirm --clean
```

The result is `dist/TransferManagementSystem.exe`. On first launch it
creates `data/`, `attachments/` and `exports/` folders next to the .exe
(or, if that folder isn't writable, under `%APPDATA%\Transfer Management
System\`) — the database persists across restarts.

### Automatically via GitHub Actions

`.github/workflows/build-exe.yml` builds the .exe on a `windows-latest`
runner:

- **On every push to `main` / every pull request** — the .exe is
  attached as a downloadable workflow artifact (Actions tab → the run →
  "Artifacts").
- **On every version tag** (e.g. `git tag v1.0.0 && git push --tags`) —
  the .exe is additionally published as an asset on a GitHub Release.
- You can also trigger it manually from the Actions tab
  (`workflow_dispatch`).

No extra repository secrets are needed — it uses the default
`GITHUB_TOKEN`.

To publish a release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

### Notes for maintainers

- The spec builds **onefile** mode (a single .exe). If startup time
  matters more than a single file, switch `build.spec` to a `COLLECT()`
  step for a faster-starting folder ("onedir") build instead.
- To brand the .exe with an icon, drop a 256×256 `icon.ico` at
  `app/resources/icon.ico` and set `icon="app/resources/icon.ico"` in
  `build.spec`.
- `app/config.py` detects `sys.frozen` (set by PyInstaller) and stores
  data next to the .exe instead of inside the temporary extraction
  folder — don't remove that check when refactoring paths.

## Notes on "Automatic Save"

Every field in the Preparation and Release modules commits to SQLite the
moment it loses focus / changes (see `DynamicForm._commit` and the
inline cell-widgets in `release_view.py` / the OEM table in
`preparation_view.py`). There is no separate "Save" button to forget to
click, and no unsaved-state to lose if the app closes unexpectedly.

## Notifications

A background timer (`MainWindow.notif_timer`, every 60s) calls
`NotificationController.scan_and_generate()`, which flags:

- Transfers due within 7 days
- Transfers past their planned date but not yet released
- Overdue PTT internal/OEM approvals
- Overdue Raw Material / Pre-check due dates

Notifications are de-duplicated by (entity, message) so re-scans don't
spam the center.
