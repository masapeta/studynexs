# SQLAlchemy models — imported here for Alembic auto-detection
from app.db.models.base import Base  # noqa: F401
from app.db.models.school import School  # noqa: F401
from app.db.models.user import User  # noqa: F401
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping  # noqa: F401
from app.db.models.student import Student, Parent, StudentParentMap  # noqa: F401
from app.db.models.teacher import Teacher  # noqa: F401
from app.db.models.attendance import Attendance  # noqa: F401
from app.db.models.examination import Exam, ExamMark  # noqa: F401
from app.db.models.fee import FeeStructure, StudentFeeRecord, FeeReceipt, ReceiptCounter  # noqa: F401
from app.db.models.timetable import TimetableSlot  # noqa: F401
from app.db.models.communication import Notice, NoticeReadReceipt  # noqa: F401
from app.db.models.school_ops import TransportRoute, StudentTransport, LibraryBook, LibraryIssue, Event  # noqa: F401
from app.db.models.outbox import OutboxEvent  # noqa: F401
from app.db.models.job import Job, JobStatus  # noqa: F401
from app.db.models.ai_usage import AIUsage  # noqa: F401
from app.db.models.ai_feedback import AIFeedback  # noqa: F401
from app.db.models.audit import AuditLog  # noqa: F401
from app.db.models.notification import Notification  # noqa: F401
from app.db.models.file import UploadedFile  # noqa: F401
