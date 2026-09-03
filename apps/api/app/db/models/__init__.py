# SQLAlchemy models — imported here for Alembic auto-detection
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping  # noqa: F401
from app.db.models.ai_feedback import AIFeedback  # noqa: F401
from app.db.models.ai_usage import AIUsage  # noqa: F401
from app.db.models.answer_sheet_evaluation import AnswerSheetEvaluation  # noqa: F401
from app.db.models.attendance import Attendance  # noqa: F401
from app.db.models.audit import AuditLog  # noqa: F401
from app.db.models.base import Base  # noqa: F401
from app.db.models.communication import Notice, NoticeReadReceipt  # noqa: F401
from app.db.models.concept_card import ConceptCard, ConceptCardStatus  # noqa: F401
from app.db.models.content_review import (  # noqa: F401
    ContentReviewItem,
    ContentReviewItemType,
    ContentReviewSource,
    ContentReviewStatus,
)
from app.db.models.curriculum_pack import (  # noqa: F401
    CurriculumChapter,
    CurriculumLearningOutcome,
    CurriculumPack,
    CurriculumPackAuditEvent,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.document_ingestion import (  # noqa: F401
    DocumentIngestion,
    DocumentType,
    IngestStatus,
)
from app.db.models.examination import Exam, ExamMark  # noqa: F401
from app.db.models.fee import (  # noqa: F401
    FeeReceipt,
    FeeStructure,
    ReceiptCounter,
    StudentFeeRecord,
)
from app.db.models.file import UploadedFile  # noqa: F401
from app.db.models.job import Job, JobStatus  # noqa: F401
from app.db.models.knowledge_graph import (  # noqa: F401
    ConceptSource,
    CurriculumConcept,
    KgEdge,
    KgEdgeType,
    KgNodeType,
)
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus  # noqa: F401
from app.db.models.mastery import (  # noqa: F401
    FlagSeverity,
    FlagStatus,
    MasteryFlag,
    MasteryTrend,
    StudentTopicMastery,
)
from app.db.models.misconception import MisconceptionEntry  # noqa: F401
from app.db.models.notification import Notification  # noqa: F401
from app.db.models.outbox import OutboxEvent  # noqa: F401
from app.db.models.question_bank import (  # noqa: F401
    BANK_STATUS_APPROVED,
    QuestionBankItem,
    QuestionSource,
    RubricBankItem,
)
from app.db.models.question_paper import PaperStatus, QuestionPaper  # noqa: F401
from app.db.models.report_card import ReportCard, ReportStatus  # noqa: F401
from app.db.models.residential import BlockGender, ResidentialBlock, RoomAllocation  # noqa: F401
from app.db.models.school import School  # noqa: F401
from app.db.models.school_ops import (  # noqa: F401
    AdmissionCandidate,
    Event,
    LibraryBook,
    LibraryIssue,
    SchoolExpense,
    StaffPayrollEntry,
    StaffProfile,
    StudentTransport,
    TransportRoute,
)
from app.db.models.student import (  # noqa: F401
    Enrollment,
    EnrollmentStatus,
    Parent,
    Student,
    StudentParentMap,
    StudentStatus,
)
from app.db.models.teacher import Teacher  # noqa: F401
from app.db.models.timetable import TimetableSlot  # noqa: F401
from app.db.models.user import User  # noqa: F401
