"""Ordered prospect tenant purge — DB, vectors, files, Redis sessions, jobs (Stage 2B)."""
from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.ai_feedback import AIFeedback
from app.db.models.ai_usage import AIUsage
from app.db.models.answer_sheet_evaluation import AnswerSheetEvaluation
from app.db.models.attendance import Attendance
from app.db.models.audit import AuditLog
from app.db.models.communication import Notice, NoticeReadReceipt
from app.db.models.concept_card import ConceptCard
from app.db.models.content_review import ContentReviewItem
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumLearningOutcome,
    CurriculumPack,
    CurriculumPackAuditEvent,
    CurriculumTopic,
)
from app.db.models.document_ingestion import DocumentIngestion
from app.db.models.examination import Exam, ExamMark
from app.db.models.fee import FeeReceipt, FeeStructure, ReceiptCounter, StudentFeeRecord
from app.db.models.file import UploadedFile
from app.db.models.job import Job, JobStatus
from app.db.models.knowledge_graph import CurriculumConcept, KgEdge
from app.db.models.lesson_plan import LessonPlan
from app.db.models.mastery import MasteryFlag, StudentTopicMastery
from app.db.models.misconception import MisconceptionEntry
from app.db.models.notification import Notification
from app.db.models.outbox import OutboxEvent
from app.db.models.question_bank import QuestionBankItem
from app.db.models.question_paper import QuestionPaper
from app.db.models.report_card import ReportCard
from app.db.models.residential import ResidentialBlock, RoomAllocation
from app.db.models.school import School
from app.db.models.school_ops import (
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
from app.db.models.student import Parent, Student, StudentParentMap
from app.db.models.teacher import Teacher
from app.db.models.timetable import TimetableSlot
from app.db.models.user import User
from app.modules.demo import PURGEABLE_TENANT_KINDS
from app.modules.files.services.file_service import UPLOAD_DIR

logger = structlog.get_logger()
settings = get_settings()


class TenantCleanupError(ValueError):
    """Cleanup refused — protected tenant or invalid state."""


class TenantCleanupService:
    def __init__(self, db: AsyncSession, redis=None) -> None:
        self.db = db
        self.redis = redis

    async def assert_purgeable(self, school_id: uuid.UUID) -> School:
        school = (
            await self.db.execute(select(School).where(School.id == school_id))
        ).scalar_one_or_none()
        if school is None:
            raise TenantCleanupError("School not found")
        if school.tenant_kind not in PURGEABLE_TENANT_KINDS:
            raise TenantCleanupError(
                f"Tenant kind {school.tenant_kind!r} is protected from automated cleanup"
            )
        protected = {s.lower() for s in settings.DEMO_PROTECTED_TENANT_SLUGS}
        if school.tenant_slug.lower() in protected:
            raise TenantCleanupError(f"Tenant slug {school.tenant_slug!r} is protected")
        return school

    async def _fail_pending_jobs(
        self, school_id: uuid.UUID, *, exclude_job_id: uuid.UUID | None = None
    ) -> int:
        stmt = (
            update(Job)
            .where(
                Job.school_id == school_id,
                Job.status.in_((JobStatus.QUEUED, JobStatus.RUNNING)),
            )
            .values(
                status=JobStatus.FAILED,
                error="tenant_cleanup",
                updated_at=datetime.now(timezone.utc),
            )
        )
        if exclude_job_id is not None:
            stmt = stmt.where(Job.id != exclude_job_id)
        result = await self.db.execute(stmt)
        return result.rowcount or 0

    async def _purge_vectors(self, school_id: uuid.UUID) -> None:
        from app.modules.ai.vectorstore import get_vector_store
        from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore
        from app.modules.ai.vectorstore.qdrant_store import QdrantVectorStore

        store = get_vector_store()
        sid = str(school_id)
        if isinstance(store, QdrantVectorStore):
            client = store._get_client()
            collections = await client.get_collections()
            for col in collections.collections:
                await store.delete(col.name, school_id=sid)
        elif isinstance(store, InMemoryVectorStore):
            for name in list(store._collections.keys()):
                await store.delete(name, school_id=sid)

    async def _purge_files(self, school_id: uuid.UUID) -> None:
        """Remove on-disk blobs after DB rows referencing uploaded_files are gone."""
        school_dir = Path(UPLOAD_DIR) / str(school_id)
        if school_dir.is_dir():
            shutil.rmtree(school_dir, ignore_errors=True)

    async def _revoke_redis_sessions(self, school_id: uuid.UUID) -> None:
        if self.redis is None:
            return
        user_ids = (
            await self.db.execute(select(User.id).where(User.school_id == school_id))
        ).scalars().all()
        prefix_refresh = settings.REDIS_REFRESH_JTI_PREFIX
        prefix_cache = settings.REDIS_USER_CACHE_PREFIX
        for uid in user_ids:
            uid_s = str(uid)
            pattern = f"{prefix_refresh}{uid_s}:*"
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
            await self.redis.delete(f"{prefix_cache}{uid_s}")

    async def _purge_database_rows(
        self, school_id: uuid.UUID, *, exclude_job_id: uuid.UUID | None = None
    ) -> None:
        """Explicit ordered deletes — FKs do not cascade from schools.id."""
        sid = school_id
        student_ids = select(Student.id).where(Student.school_id == sid)
        parent_ids = select(Parent.id).where(Parent.school_id == sid)
        route_ids = select(TransportRoute.id).where(TransportRoute.school_id == sid)

        # Evaluation & assessment leaf tables
        await self.db.execute(
            delete(AnswerSheetEvaluation).where(AnswerSheetEvaluation.school_id == sid)
        )
        await self.db.execute(delete(ExamMark).where(ExamMark.school_id == sid))
        await self.db.execute(delete(Exam).where(Exam.school_id == sid))
        await self.db.execute(delete(QuestionPaper).where(QuestionPaper.school_id == sid))
        await self.db.execute(delete(QuestionBankItem).where(QuestionBankItem.school_id == sid))
        await self.db.execute(delete(LessonPlan).where(LessonPlan.school_id == sid))
        await self.db.execute(delete(AIUsage).where(AIUsage.school_id == sid))
        await self.db.execute(delete(AIFeedback).where(AIFeedback.school_id == sid))
        await self.db.execute(delete(KgEdge).where(KgEdge.school_id == sid))
        await self.db.execute(delete(CurriculumConcept).where(CurriculumConcept.school_id == sid))
        await self.db.execute(delete(ConceptCard).where(ConceptCard.school_id == sid))
        await self.db.execute(delete(DocumentIngestion).where(DocumentIngestion.school_id == sid))
        await self.db.execute(delete(ContentReviewItem).where(ContentReviewItem.school_id == sid))
        await self.db.execute(
            delete(CurriculumPackAuditEvent).where(CurriculumPackAuditEvent.school_id == sid)
        )
        await self.db.execute(
            delete(CurriculumLearningOutcome).where(CurriculumLearningOutcome.school_id == sid)
        )
        await self.db.execute(delete(CurriculumTopic).where(CurriculumTopic.school_id == sid))
        await self.db.execute(delete(CurriculumChapter).where(CurriculumChapter.school_id == sid))
        await self.db.execute(delete(CurriculumPack).where(CurriculumPack.school_id == sid))
        await self.db.execute(delete(MasteryFlag).where(MasteryFlag.school_id == sid))
        await self.db.execute(
            delete(StudentTopicMastery).where(StudentTopicMastery.school_id == sid)
        )
        await self.db.execute(delete(MisconceptionEntry).where(MisconceptionEntry.school_id == sid))
        await self.db.execute(delete(ReportCard).where(ReportCard.school_id == sid))
        await self.db.execute(delete(Attendance).where(Attendance.school_id == sid))
        await self.db.execute(delete(StudentFeeRecord).where(StudentFeeRecord.school_id == sid))
        await self.db.execute(delete(FeeReceipt).where(FeeReceipt.school_id == sid))
        await self.db.execute(delete(FeeStructure).where(FeeStructure.school_id == sid))
        await self.db.execute(delete(ReceiptCounter).where(ReceiptCounter.school_id == sid))
        await self.db.execute(delete(Notification).where(Notification.school_id == sid))
        await self.db.execute(
            delete(NoticeReadReceipt).where(
                NoticeReadReceipt.notice_id.in_(select(Notice.id).where(Notice.school_id == sid))
            )
        )
        await self.db.execute(delete(Notice).where(Notice.school_id == sid))
        await self.db.execute(delete(LibraryIssue).where(LibraryIssue.school_id == sid))
        await self.db.execute(delete(LibraryBook).where(LibraryBook.school_id == sid))
        await self.db.execute(
            delete(StudentTransport).where(
                StudentTransport.student_id.in_(student_ids)
                | StudentTransport.route_id.in_(route_ids)
            )
        )
        await self.db.execute(delete(TransportRoute).where(TransportRoute.school_id == sid))
        await self.db.execute(delete(Event).where(Event.school_id == sid))
        await self.db.execute(delete(AdmissionCandidate).where(AdmissionCandidate.school_id == sid))
        await self.db.execute(delete(StaffPayrollEntry).where(StaffPayrollEntry.school_id == sid))
        await self.db.execute(delete(StaffProfile).where(StaffProfile.school_id == sid))
        await self.db.execute(delete(SchoolExpense).where(SchoolExpense.school_id == sid))
        await self.db.execute(delete(RoomAllocation).where(RoomAllocation.school_id == sid))
        await self.db.execute(delete(ResidentialBlock).where(ResidentialBlock.school_id == sid))
        await self.db.execute(delete(TimetableSlot).where(TimetableSlot.school_id == sid))
        await self.db.execute(
            delete(StudentParentMap).where(
                StudentParentMap.student_id.in_(student_ids)
                | StudentParentMap.parent_id.in_(parent_ids)
            )
        )
        await self.db.execute(delete(Student).where(Student.school_id == sid))
        await self.db.execute(delete(Parent).where(Parent.school_id == sid))
        await self.db.execute(delete(Teacher).where(Teacher.school_id == sid))
        await self.db.execute(
            delete(TeacherSubjectMapping).where(TeacherSubjectMapping.school_id == sid)
        )
        await self.db.execute(
            update(Class).where(Class.school_id == sid).values(class_incharge_id=None)
        )
        await self.db.execute(delete(Subject).where(Subject.school_id == sid))
        await self.db.execute(delete(Class).where(Class.school_id == sid))
        await self.db.execute(delete(AcademicYear).where(AcademicYear.school_id == sid))
        await self.db.execute(delete(AuditLog).where(AuditLog.school_id == sid))
        # Best-effort outbox purge when payload carries school_id.
        await self.db.execute(
            delete(OutboxEvent).where(OutboxEvent.payload["school_id"].as_string() == str(sid))
        )
        job_delete = delete(Job).where(Job.school_id == sid)
        if exclude_job_id is not None:
            job_delete = job_delete.where(Job.id != exclude_job_id)
        await self.db.execute(job_delete)
        await self.db.execute(delete(UploadedFile).where(UploadedFile.school_id == sid))
        await self.db.execute(delete(User).where(User.school_id == sid))
        await self.db.execute(delete(School).where(School.id == sid))

    async def purge_prospect_tenant(
        self, school_id: uuid.UUID, *, exclude_job_id: uuid.UUID | None = None
    ) -> dict:
        school = (
            await self.db.execute(select(School).where(School.id == school_id))
        ).scalar_one_or_none()
        if school is None:
            return {
                "school_id": str(school_id),
                "tenant_slug": None,
                "jobs_failed": 0,
                "already_purged": True,
            }

        await self.assert_purgeable(school_id)
        slug = school.tenant_slug

        jobs_failed = await self._fail_pending_jobs(school_id, exclude_job_id=exclude_job_id)
        await self._purge_vectors(school_id)
        await self._revoke_redis_sessions(school_id)
        # DB rows first — DocumentIngestion, StaffProfile, and SchoolExpense FK uploaded_files.
        await self._purge_database_rows(school_id, exclude_job_id=exclude_job_id)
        await self._purge_files(school_id)
        await self.db.commit()

        logger.info(
            "prospect_tenant_purged",
            school_id=str(school_id),
            tenant_slug=slug,
            jobs_failed=jobs_failed,
            exclude_job_id=str(exclude_job_id) if exclude_job_id else None,
        )
        return {"school_id": str(school_id), "tenant_slug": slug, "jobs_failed": jobs_failed}
