"""
Import every model module here so that Base.metadata is fully populated
before app.database.init_db() calls create_all().
"""
from app.models.base import Base  # noqa: F401
from app.models.transfer import Transfer, Tool, PartNumber  # noqa: F401
from app.models.ptt_approval import PTTApproval, OEMApproval  # noqa: F401
from app.models.safety_stock import SafetyStock  # noqa: F401
from app.models.raw_material import RawMaterial  # noqa: F401
from app.models.pre_check import PreCheck  # noqa: F401
from app.models.e2e_followup import E2EFollowUp  # noqa: F401
from app.models.applicator import Applicator, CounterPart  # noqa: F401
from app.models.training import Training  # noqa: F401
from app.models.release import ReleaseChecklist, ReleaseItem  # noqa: F401
from app.models.collab import Attachment, Comment, HistoryLog, Notification  # noqa: F401
