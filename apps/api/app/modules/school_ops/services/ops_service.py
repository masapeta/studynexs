"""School operations service — library, events."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pii import mask_aadhaar, mask_id_number
from app.core.tenant_scope import TenantScope
from app.db.models.file import FileCategory
from app.db.models.residential import BlockGender, ResidentialBlock, RoomAllocation
from app.db.models.school_ops import (
    ADMISSION_STAGE_ORDER,
    AdmissionCandidate,
    AdmissionStage,
    Event,
    LibraryBook,
    LibraryIssue,
    LibraryIssueStatus,
    PayrollStatus,
    SchoolExpense,
    StaffPayrollEntry,
    StaffProfile,
    StudentTransport,
    TransportRoute,
)
from app.db.models.student import Student
from app.db.models.teacher import Teacher
from app.db.models.user import User, UserRole
from app.modules.files.services.file_service import FileService
from app.modules.files.services.file_validation import read_file_bytes_bounded
from app.modules.school_ops.schemas.ops import (
    AdmissionCandidateCreate,
    AppliedStageDetails,
    EnrolledStageDetails,
    EventCreate,
    InterviewStageDetails,
    LibraryBookCreate,
    OfferStageDetails,
    ResidentialAllocateRequest,
    ResidentialBlockCreate,
    SchoolExpenseCreate,
    StaffOnboardCreate,
    TransportAssignRequest,
    TransportRouteCreate,
)
from app.modules.school_ops.services.admission_document_extract import extract_document_number


class SchoolOpsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Library ──────────────────────────────────────────────────

    async def list_books(self, school_id: uuid.UUID, search: str | None = None) -> list[dict]:
        query = select(LibraryBook).where(LibraryBook.school_id == school_id)
        if search:
            query = query.where(LibraryBook.title.ilike(f"%{search}%"))
        books = (
            (await self.db.execute(query.order_by(LibraryBook.title).limit(100))).scalars().all()
        )
        if not books:
            return []
        book_ids = [b.id for b in books]
        issued_rows = (
            await self.db.execute(
                select(LibraryIssue.book_id, User.full_name)
                .join(User, User.id == LibraryIssue.user_id)
                .where(
                    LibraryIssue.school_id == school_id,
                    LibraryIssue.book_id.in_(book_ids),
                    LibraryIssue.status == LibraryIssueStatus.ISSUED,
                )
            )
        ).all()
        issued_map: dict[uuid.UUID, list[str]] = {}
        for book_id, name in issued_rows:
            issued_map.setdefault(book_id, []).append(name)
        return [
            {
                "id": str(b.id),
                "title": b.title,
                "author": b.author,
                "isbn": b.isbn,
                "category": b.category,
                "total_copies": b.total_copies,
                "available_copies": b.available_copies,
                "issued_to": issued_map.get(b.id, []),
            }
            for b in books
        ]

    async def add_book(self, school_id: uuid.UUID, data: LibraryBookCreate) -> LibraryBook:
        book = LibraryBook(
            school_id=school_id,
            title=data.title,
            author=data.author,
            isbn=data.isbn,
            category=data.category,
            total_copies=data.total_copies,
            available_copies=data.total_copies,
        )
        self.db.add(book)
        await self.db.flush()
        return book

    async def issue_book(
        self, school_id: uuid.UUID, book_id: uuid.UUID, user_id: uuid.UUID
    ) -> LibraryIssue:
        await TenantScope(self.db, school_id).user_in_school(user_id)
        book = (
            await self.db.execute(
                select(LibraryBook)
                .where(LibraryBook.id == book_id, LibraryBook.school_id == school_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not book or book.available_copies <= 0:
            raise ValueError("Book not available")
        book.available_copies -= 1
        issue = LibraryIssue(
            school_id=school_id,
            book_id=book_id,
            user_id=user_id,
            status=LibraryIssueStatus.ISSUED,
        )
        self.db.add(issue)
        await self.db.flush()
        return issue

    async def return_book(self, school_id: uuid.UUID, issue_id: uuid.UUID) -> None:
        issue = (
            await self.db.execute(
                select(LibraryIssue)
                .where(LibraryIssue.id == issue_id, LibraryIssue.school_id == school_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not issue:
            raise ValueError("Issue record not found")
        if issue.status == LibraryIssueStatus.RETURNED:
            return
        issue.status = LibraryIssueStatus.RETURNED
        issue.returned_at = datetime.now(timezone.utc)
        book = (
            await self.db.execute(
                select(LibraryBook)
                .where(LibraryBook.id == issue.book_id, LibraryBook.school_id == school_id)
                .with_for_update()
            )
        ).scalar_one()
        if book.available_copies < book.total_copies:
            book.available_copies += 1
        await self.db.flush()

    # ── Events ───────────────────────────────────────────────────

    async def list_events(self, school_id: uuid.UUID) -> list[Event]:
        result = await self.db.execute(
            select(Event)
            .where(Event.school_id == school_id)
            .order_by(Event.event_date.desc())
            .limit(50)
        )
        return list(result.scalars().all())

    async def create_event(
        self, school_id: uuid.UUID, data: EventCreate, created_by: uuid.UUID
    ) -> Event:
        event = Event(
            school_id=school_id,
            title=data.title,
            description=data.description,
            event_date=data.event_date,
            venue=data.venue,
            target_roles=data.target_roles,
            created_by=created_by,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    # ── Transport ────────────────────────────────────────────────

    async def list_transport_routes(self, school_id: uuid.UUID) -> list[dict]:
        routes = (
            (
                await self.db.execute(
                    select(TransportRoute)
                    .where(TransportRoute.school_id == school_id)
                    .order_by(TransportRoute.route_name)
                )
            )
            .scalars()
            .all()
        )
        route_ids = [r.id for r in routes]
        counts: dict = {}
        names_map: dict[uuid.UUID, list[str]] = {}
        if route_ids:
            rows = (
                await self.db.execute(
                    select(StudentTransport.route_id, func.count())
                    .where(StudentTransport.route_id.in_(route_ids))
                    .group_by(StudentTransport.route_id)
                )
            ).all()
            counts = {rid: c for rid, c in rows}
            name_rows = (
                await self.db.execute(
                    select(StudentTransport.route_id, User.full_name)
                    .join(Student, Student.id == StudentTransport.student_id)
                    .join(User, User.id == Student.user_id)
                    .where(StudentTransport.route_id.in_(route_ids))
                    .order_by(User.full_name)
                )
            ).all()
            for rid, name in name_rows:
                names_map.setdefault(rid, []).append(name.split()[0])
        return [
            {
                "id": str(r.id),
                "route_name": r.route_name,
                "vehicle_number": r.vehicle_number,
                "driver_name": r.driver_name,
                "driver_contact": r.driver_contact,
                "stops": r.stops or [],
                "capacity": r.capacity,
                "is_active": r.is_active,
                "student_count": counts.get(r.id, 0),
                "student_names": names_map.get(r.id, []),
            }
            for r in routes
        ]

    async def create_route(
        self, school_id: uuid.UUID, data: TransportRouteCreate
    ) -> TransportRoute:
        route = TransportRoute(
            school_id=school_id,
            route_name=data.route_name,
            vehicle_number=data.vehicle_number,
            driver_name=data.driver_name,
            driver_contact=data.driver_contact,
            stops=data.stops or [],
            capacity=data.capacity or 30,
        )
        self.db.add(route)
        await self.db.flush()
        return route

    async def list_route_students(self, school_id: uuid.UUID, route_id: uuid.UUID) -> list[dict]:
        route = (
            await self.db.execute(
                select(TransportRoute).where(
                    TransportRoute.id == route_id, TransportRoute.school_id == school_id
                )
            )
        ).scalar_one_or_none()
        if not route:
            raise ValueError("Route not found")
        rows = (
            await self.db.execute(
                select(StudentTransport, User.full_name, Student.admission_no)
                .join(Student, Student.id == StudentTransport.student_id)
                .join(User, User.id == Student.user_id)
                .where(StudentTransport.route_id == route_id)
                .order_by(Student.admission_no)
            )
        ).all()
        return [
            {
                "student_id": str(st.student_id),
                "name": name,
                "admission_no": adm,
                "boarding_stop": st.boarding_stop,
            }
            for st, name, adm in rows
        ]

    async def assign_student_transport(
        self, school_id: uuid.UUID, data: TransportAssignRequest
    ) -> StudentTransport:
        route = (
            await self.db.execute(
                select(TransportRoute).where(
                    TransportRoute.id == data.route_id, TransportRoute.school_id == school_id
                )
            )
        ).scalar_one_or_none()
        if not route:
            raise ValueError("Route not found")
        student = (
            await self.db.execute(
                select(Student).where(Student.id == data.student_id, Student.school_id == school_id)
            )
        ).scalar_one_or_none()
        if not student:
            raise ValueError("Student not found")
        existing = (
            await self.db.execute(
                select(StudentTransport).where(StudentTransport.student_id == data.student_id)
            )
        ).scalar_one_or_none()
        if existing:
            existing.route_id = data.route_id
            existing.boarding_stop = data.boarding_stop
            await self.db.flush()
            return existing
        st = StudentTransport(
            student_id=data.student_id,
            route_id=data.route_id,
            boarding_stop=data.boarding_stop,
        )
        self.db.add(st)
        await self.db.flush()
        return st

    # ── Residential ──────────────────────────────────────────────

    async def list_residential_blocks(self, school_id: uuid.UUID) -> list[dict]:
        blocks = (
            (
                await self.db.execute(
                    select(ResidentialBlock)
                    .where(ResidentialBlock.school_id == school_id)
                    .order_by(ResidentialBlock.block_name)
                )
            )
            .scalars()
            .all()
        )
        block_ids = [b.id for b in blocks]
        counts: dict = {}
        if block_ids:
            rows = (
                await self.db.execute(
                    select(RoomAllocation.block_id, func.count())
                    .where(RoomAllocation.block_id.in_(block_ids))
                    .group_by(RoomAllocation.block_id)
                )
            ).all()
            counts = {bid: c for bid, c in rows}
        return [
            {
                "id": str(b.id),
                "block_name": b.block_name,
                "block_gender": b.block_gender.value if b.block_gender else "mixed",
                "warden_name": b.warden_name,
                "warden_contact": b.warden_contact,
                "total_rooms": b.total_rooms,
                "is_active": b.is_active,
                "resident_count": counts.get(b.id, 0),
            }
            for b in blocks
        ]

    async def create_block(
        self, school_id: uuid.UUID, data: ResidentialBlockCreate
    ) -> ResidentialBlock:
        try:
            gender = BlockGender(data.block_gender)
        except ValueError:
            gender = BlockGender.MIXED
        block = ResidentialBlock(
            school_id=school_id,
            block_name=data.block_name,
            block_gender=gender,
            warden_name=data.warden_name,
            warden_contact=data.warden_contact,
            total_rooms=data.total_rooms,
        )
        self.db.add(block)
        await self.db.flush()
        return block

    async def list_block_residents(self, school_id: uuid.UUID, block_id: uuid.UUID) -> list[dict]:
        block = (
            await self.db.execute(
                select(ResidentialBlock).where(
                    ResidentialBlock.id == block_id, ResidentialBlock.school_id == school_id
                )
            )
        ).scalar_one_or_none()
        if not block:
            raise ValueError("Block not found")
        rows = (
            await self.db.execute(
                select(RoomAllocation, User.full_name, Student.admission_no)
                .join(Student, Student.id == RoomAllocation.student_id)
                .join(User, User.id == Student.user_id)
                .where(RoomAllocation.block_id == block_id)
                .order_by(RoomAllocation.room_number)
            )
        ).all()
        return [
            {
                "student_id": str(a.student_id),
                "name": name,
                "admission_no": adm,
                "room_number": a.room_number,
            }
            for a, name, adm in rows
        ]

    async def allocate_resident(
        self, school_id: uuid.UUID, data: ResidentialAllocateRequest
    ) -> RoomAllocation:
        block = (
            await self.db.execute(
                select(ResidentialBlock).where(
                    ResidentialBlock.id == data.block_id,
                    ResidentialBlock.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not block:
            raise ValueError("Block not found")
        student = (
            await self.db.execute(
                select(Student).where(Student.id == data.student_id, Student.school_id == school_id)
            )
        ).scalar_one_or_none()
        if not student:
            raise ValueError("Student not found")
        existing = (
            await self.db.execute(
                select(RoomAllocation).where(RoomAllocation.student_id == data.student_id)
            )
        ).scalar_one_or_none()
        if existing:
            existing.block_id = data.block_id
            existing.room_number = data.room_number
            await self.db.flush()
            return existing
        alloc = RoomAllocation(
            school_id=school_id,
            student_id=data.student_id,
            block_id=data.block_id,
            room_number=data.room_number,
        )
        self.db.add(alloc)
        await self.db.flush()
        return alloc

    # ── Admissions ───────────────────────────────────────────────

    _STAGE_DETAIL_MODELS = {
        AdmissionStage.APPLIED: AppliedStageDetails,
        AdmissionStage.INTERVIEW: InterviewStageDetails,
        AdmissionStage.OFFER: OfferStageDetails,
        AdmissionStage.ENROLLED: EnrolledStageDetails,
    }

    def _serialize_stage_details(self, details: dict | None) -> dict:
        if not details:
            return {}
        out: dict = {}
        for stage_key, payload in details.items():
            if not isinstance(payload, dict):
                continue
            serialized: dict = {}
            for key, value in payload.items():
                if isinstance(value, date):
                    serialized[key] = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    serialized[key] = str(value)
                else:
                    serialized[key] = value
            out[stage_key] = serialized
        return out

    def _validate_stage_details(self, stage: AdmissionStage, details: dict) -> dict:
        model = self._STAGE_DETAIL_MODELS.get(stage)
        if not model:
            raise ValueError(f"No additional details expected for stage {stage.value}")
        parsed = model.model_validate(details)
        return parsed.model_dump(mode="json")

    def _stage_requires_details(self, stage: AdmissionStage) -> bool:
        return stage in self._STAGE_DETAIL_MODELS

    def _mask_identity_in_stage_details(self, details: dict) -> dict:
        out = dict(details)
        applied = out.get("applied")
        if not isinstance(applied, dict):
            return out
        masked = dict(applied)
        if masked.get("aadhaar_number"):
            masked["aadhaar_number"] = mask_aadhaar(str(masked["aadhaar_number"]))
        if masked.get("birth_certificate_number"):
            masked["birth_certificate_number"] = mask_id_number(
                str(masked["birth_certificate_number"])
            )
        if masked.get("apaar_number"):
            masked["apaar_number"] = mask_id_number(str(masked["apaar_number"]))
        out["applied"] = masked
        return out

    def admission_to_dict(self, r: AdmissionCandidate, *, mask_stage_pii: bool = True) -> dict:
        stage_details = self._serialize_stage_details(r.stage_details or {})
        if mask_stage_pii:
            stage_details = self._mask_identity_in_stage_details(stage_details)
        return {
            "id": str(r.id),
            "name": r.name,
            "grade_applied": r.grade_applied,
            "stage": r.stage.value,
            "enquiry_date": r.enquiry_date.isoformat(),
            "date_of_birth": r.date_of_birth.isoformat() if r.date_of_birth else None,
            "gender": r.gender,
            "parent_name": r.parent_name,
            "parent_relation": r.parent_relation,
            "parent_occupation": r.parent_occupation,
            "parent_mobile": r.parent_mobile,
            "parent_email": r.parent_email,
            "address_line": r.address_line,
            "city": r.city,
            "previous_school_name": r.previous_school_name,
            "previous_grade": r.previous_grade,
            "enquiry_source": r.enquiry_source,
            "aadhaar_number": mask_aadhaar(r.aadhaar_number),
            "birth_certificate_number": mask_id_number(r.birth_certificate_number),
            "apaar_number": mask_id_number(r.apaar_number),
            "notes": r.notes,
            "stage_details": stage_details,
        }

    def _admission_to_dict(self, r: AdmissionCandidate) -> dict:
        return self.admission_to_dict(r, mask_stage_pii=True)

    async def list_admissions(self, school_id: uuid.UUID) -> list[dict]:
        rows = (
            (
                await self.db.execute(
                    select(AdmissionCandidate)
                    .where(AdmissionCandidate.school_id == school_id)
                    .order_by(AdmissionCandidate.enquiry_date.desc())
                )
            )
            .scalars()
            .all()
        )
        return [self._admission_to_dict(r) for r in rows]

    def _sync_applied_identity_fields(self, row: AdmissionCandidate, applied: dict) -> None:
        row.aadhaar_number = applied.get("aadhaar_number")
        row.birth_certificate_number = applied.get("birth_certificate_number")
        row.apaar_number = applied.get("apaar_number")

    async def extract_admission_document_number(
        self,
        school_id: uuid.UUID,
        file_id: uuid.UUID,
        document_type: str,
    ) -> str | None:
        file_service = FileService(self.db)
        record = await file_service.get_file(file_id, school_id)
        if not record:
            raise ValueError("File not found")
        if record.category not in (FileCategory.DOCUMENT, FileCategory.REPORT_CARD):
            raise ValueError("File is not an admission identity document")

        file_data = read_file_bytes_bounded(
            record.storage_path,
            size_bytes=record.size_bytes,
        )
        return await extract_document_number(
            file_data=file_data,
            content_type=record.content_type,
            doc_type=document_type,
        )

    async def create_admission(
        self, school_id: uuid.UUID, data: AdmissionCandidateCreate, created_by: uuid.UUID
    ) -> AdmissionCandidate:
        mobile = "".join(ch for ch in data.parent_mobile if ch.isdigit())
        row = AdmissionCandidate(
            school_id=school_id,
            name=data.name.strip(),
            grade_applied=data.grade_applied.strip(),
            stage=AdmissionStage.ENQUIRY,
            enquiry_date=data.enquiry_date,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            parent_name=data.parent_name.strip(),
            parent_relation=data.parent_relation,
            parent_occupation=data.parent_occupation.strip() if data.parent_occupation else None,
            parent_mobile=mobile,
            parent_email=data.parent_email.strip() if data.parent_email else None,
            address_line=data.address_line.strip() if data.address_line else None,
            city=data.city.strip() if data.city else None,
            previous_school_name=data.previous_school_name.strip()
            if data.previous_school_name
            else None,
            previous_grade=data.previous_grade.strip() if data.previous_grade else None,
            enquiry_source=data.enquiry_source,
            notes=data.notes.strip() if data.notes else None,
            stage_details={},
            created_by=created_by,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def advance_admission(
        self, school_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> AdmissionCandidate:
        row = await self._get_admission_candidate(school_id, candidate_id)
        idx = ADMISSION_STAGE_ORDER.index(row.stage)
        if idx >= len(ADMISSION_STAGE_ORDER) - 1:
            raise ValueError("Already enrolled")
        row.stage = ADMISSION_STAGE_ORDER[idx + 1]
        await self.db.flush()
        return row

    async def revert_admission(
        self, school_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> AdmissionCandidate:
        row = await self._get_admission_candidate(school_id, candidate_id)
        idx = ADMISSION_STAGE_ORDER.index(row.stage)
        if idx <= 0:
            raise ValueError("Already at enquiry")
        row.stage = ADMISSION_STAGE_ORDER[idx - 1]
        await self.db.flush()
        return row

    def _has_saved_stage_details(self, row: AdmissionCandidate, stage: AdmissionStage) -> bool:
        """True when this stage was completed before (details exist for it or a later stage)."""
        details = row.stage_details or {}
        existing = details.get(stage.value)
        if isinstance(existing, dict) and existing:
            return True

        stage_idx = ADMISSION_STAGE_ORDER.index(stage)
        for later in ADMISSION_STAGE_ORDER[stage_idx + 1 :]:
            later_data = details.get(later.value)
            if isinstance(later_data, dict) and later_data:
                return True
        return False

    async def update_admission_stage(
        self,
        school_id: uuid.UUID,
        candidate_id: uuid.UUID,
        stage: AdmissionStage,
        details: dict | None = None,
    ) -> AdmissionCandidate:
        row = await self._get_admission_candidate(school_id, candidate_id)
        if row.stage == stage:
            return row

        old_idx = ADMISSION_STAGE_ORDER.index(row.stage)
        new_idx = ADMISSION_STAGE_ORDER.index(stage)

        if abs(new_idx - old_idx) != 1:
            raise ValueError("Candidates can only move one stage at a time")

        if self._stage_requires_details(stage):
            if details is not None:
                validated = self._validate_stage_details(stage, details)
                merged = dict(row.stage_details or {})
                merged[stage.value] = validated
                row.stage_details = merged
                if stage == AdmissionStage.APPLIED:
                    self._sync_applied_identity_fields(row, validated)
            elif not self._has_saved_stage_details(row, stage):
                label = stage.value.replace("_", " ")
                raise ValueError(f"Additional details are required when moving to {label}")

        row.stage = stage
        await self.db.flush()
        return row

    async def _get_admission_candidate(
        self, school_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> AdmissionCandidate:
        row = (
            await self.db.execute(
                select(AdmissionCandidate).where(
                    AdmissionCandidate.id == candidate_id,
                    AdmissionCandidate.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not row:
            raise ValueError("Candidate not found")
        return row

    def admission_pipeline_counts(self, rows: list[dict]) -> dict[str, int]:
        counts = {s.value: 0 for s in AdmissionStage}
        for r in rows:
            counts[r["stage"]] = counts.get(r["stage"], 0) + 1
        return counts

    # ── Payroll ──────────────────────────────────────────────────

    # Suggested starting salaries used only when generating a month's payroll. Decimal, never
    # float — money is exact end to end. These are defaults a school edits, not authoritative.
    _DEFAULT_GROSS: dict[str, Decimal] = {
        "super_admin": Decimal("145000"),
        "admin": Decimal("85000"),
        "class_incharge": Decimal("65000"),
        "teacher": Decimal("62000"),
        "operations": Decimal("45000"),
    }
    _FALLBACK_GROSS = Decimal("50000")
    # Payroll covers salaried operational staff; principals (super_admin) are excluded here,
    # preserving the original behavior. The super_admin default above is kept for the day that
    # policy changes, but is intentionally unreachable today.
    _STAFF_ROLES = ("teacher", "class_incharge", "admin", "operations")

    async def _active_staff(self, school_id: uuid.UUID) -> list[User]:
        return list(
            (
                await self.db.execute(
                    select(User)
                    .where(
                        User.school_id == school_id,
                        User.role.in_(self._STAFF_ROLES),
                        User.is_active.is_(True),
                    )
                    .order_by(User.full_name)
                )
            )
            .scalars()
            .all()
        )

    async def list_payroll(
        self, school_id: uuid.UUID, period_month: date | None = None
    ) -> list[dict]:
        """Read-only payroll view for the month.

        Staff without a saved entry are projected in memory as ``not_generated`` with a
        suggested gross and ``entry_id: None`` — this endpoint must never create or persist
        payroll rows (a GET silently minting salary liabilities was a real defect). Use
        ``generate_payroll`` to create the month's entries explicitly.
        """
        month = period_month or date.today().replace(day=1)
        users = await self._active_staff(school_id)
        entries = (
            (
                await self.db.execute(
                    select(StaffPayrollEntry).where(
                        StaffPayrollEntry.school_id == school_id,
                        StaffPayrollEntry.period_month == month,
                    )
                )
            )
            .scalars()
            .all()
        )
        entry_map = {e.user_id: e for e in entries}

        result: list[dict] = []
        for u in users:
            role_key = u.role.value
            e = entry_map.get(u.id)
            if e:
                result.append(
                    {
                        "user_id": str(u.id),
                        "name": u.full_name,
                        "role": role_key.replace("_", " "),
                        # Keep money exact in the service; the endpoint owns wire serialization.
                        "gross_amount": e.gross_amount,
                        "status": e.status.value,
                        "entry_id": str(e.id),
                    }
                )
            else:
                result.append(
                    {
                        "user_id": str(u.id),
                        "name": u.full_name,
                        "role": role_key.replace("_", " "),
                        "gross_amount": self._DEFAULT_GROSS.get(
                            role_key, self._FALLBACK_GROSS
                        ),
                        "status": "not_generated",
                        "entry_id": None,
                    }
                )
        return result

    async def generate_payroll(self, school_id: uuid.UUID, period_month: date | None = None) -> int:
        """Explicitly create payroll entries for staff missing one this month. Idempotent.

        Uses INSERT ... ON CONFLICT DO NOTHING against uq_payroll_user_month so concurrent
        calls (or a retry) can't double-create or 500 on the unique constraint. Returns the
        number of new entries created.
        """
        month = period_month or date.today().replace(day=1)
        users = await self._active_staff(school_id)
        existing_ids = {
            uid
            for (uid,) in (
                await self.db.execute(
                    select(StaffPayrollEntry.user_id).where(
                        StaffPayrollEntry.school_id == school_id,
                        StaffPayrollEntry.period_month == month,
                    )
                )
            ).all()
        }
        created = 0
        for u in users:
            if u.id in existing_ids:
                continue
            gross = self._DEFAULT_GROSS.get(u.role.value, self._FALLBACK_GROSS)
            res = await self.db.execute(
                pg_insert(StaffPayrollEntry)
                .values(
                    school_id=school_id,
                    user_id=u.id,
                    period_month=month,
                    gross_amount=gross,
                    status=PayrollStatus.PENDING,
                )
                .on_conflict_do_nothing(constraint="uq_payroll_user_month")
            )
            # Count only rows that actually inserted — ON CONFLICT DO NOTHING no-ops a row that
            # a concurrent generate created between our pre-fetch and this insert, so trust
            # rowcount over the intended count.
            created += res.rowcount or 0
        await self.db.flush()
        return created

    async def mark_payroll_paid(
        self, school_id: uuid.UUID, entry_id: uuid.UUID
    ) -> StaffPayrollEntry:
        row = (
            await self.db.execute(
                select(StaffPayrollEntry).where(
                    StaffPayrollEntry.id == entry_id,
                    StaffPayrollEntry.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not row:
            raise ValueError("Payroll entry not found")
        row.status = PayrollStatus.PAID
        row.paid_at = datetime.now(timezone.utc)
        await self.db.flush()
        return row

    # ── Expenses ─────────────────────────────────────────────────

    async def list_expenses(self, school_id: uuid.UUID, limit: int = 50) -> list[dict]:
        rows = (
            (
                await self.db.execute(
                    select(SchoolExpense)
                    .where(SchoolExpense.school_id == school_id)
                    .order_by(SchoolExpense.expense_date.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": str(r.id),
                "vendor": r.vendor,
                "category": r.category,
                "amount": r.amount,
                "expense_date": r.expense_date.isoformat(),
                "receipt_file_id": str(r.receipt_file_id) if r.receipt_file_id else None,
            }
            for r in rows
        ]

    async def add_expense(
        self, school_id: uuid.UUID, data: SchoolExpenseCreate, created_by: uuid.UUID
    ) -> SchoolExpense:
        row = SchoolExpense(
            school_id=school_id,
            vendor=data.vendor,
            category=data.category,
            # Pydantic validates the v1 JSON number into Decimal before it enters
            # the monetary domain, so no binary-float arithmetic reaches storage.
            amount=data.amount,
            expense_date=data.expense_date,
            receipt_file_id=data.receipt_file_id,
            created_by=created_by,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def expenses_month_total(self, school_id: uuid.UUID) -> Decimal:
        from datetime import date as date_cls

        today = date_cls.today()
        month_start = today.replace(day=1)
        total = await self.db.scalar(
            select(func.coalesce(func.sum(SchoolExpense.amount), 0)).where(
                SchoolExpense.school_id == school_id,
                SchoolExpense.expense_date >= month_start,
            )
        )
        if isinstance(total, Decimal):
            return total
        return Decimal(str(total or 0))

    # ── Staff directory ──────────────────────────────────────────

    async def _validate_staff_document(
        self, school_id: uuid.UUID, file_id: uuid.UUID | None
    ) -> None:
        if not file_id:
            return
        file_service = FileService(self.db)
        record = await file_service.get_file(file_id, school_id)
        if not record:
            raise ValueError("Uploaded document not found")
        if record.category not in (FileCategory.DOCUMENT, FileCategory.REPORT_CARD):
            raise ValueError("Invalid document file type")

    async def onboard_staff(
        self, school_id: uuid.UUID, data: StaffOnboardCreate, created_by: uuid.UUID
    ) -> dict:
        from app.modules.users.schemas.user import UserCreate
        from app.modules.users.services.user_service import UserService

        await self._validate_staff_document(school_id, data.aadhaar_document_file_id)
        await self._validate_staff_document(school_id, data.experience_document_file_id)

        role = UserRole(data.role)
        mobile = "".join(ch for ch in data.mobile if ch.isdigit())
        if len(mobile) < 10:
            raise ValueError("Enter a valid mobile number")
        full_name = f"{data.first_name.strip()} {data.last_name.strip()}".strip()

        user_service = UserService(self.db)
        user = await user_service.create_user(
            school_id,
            UserCreate(
                mobile=mobile,
                email=data.email.strip() if data.email else None,
                full_name=full_name,
                role=role,
            ),
        )

        joining = data.joining_date or date.today()
        dept_defaults = {
            UserRole.ADMIN: "Administration",
            UserRole.CLASS_INCHARGE: "Academics",
            UserRole.TEACHER: "Academics",
            UserRole.OPERATIONS: "Operations",
        }
        department = (data.department or "").strip() or dept_defaults.get(role, "Administration")

        profile = StaffProfile(
            school_id=school_id,
            user_id=user.id,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            aadhaar_number=data.aadhaar_number,
            address_line=data.address_line.strip() if data.address_line else None,
            city=data.city.strip() if data.city else None,
            qualification=data.qualification.strip() if data.qualification else None,
            department=department,
            employee_id=data.employee_id.strip() if data.employee_id else None,
            joining_date=joining,
            previous_experience=data.previous_experience.strip()
            if data.previous_experience
            else None,
            aadhaar_document_file_id=data.aadhaar_document_file_id,
            experience_document_file_id=data.experience_document_file_id,
            created_by=created_by,
        )
        self.db.add(profile)

        if role in (UserRole.TEACHER, UserRole.CLASS_INCHARGE):
            self.db.add(
                Teacher(
                    school_id=school_id,
                    user_id=user.id,
                    employee_id=profile.employee_id,
                    qualification=profile.qualification,
                    department=department,
                    joining_date=joining,
                )
            )

        await self.db.flush()
        return {"id": str(user.id), "full_name": user.full_name}

    async def list_staff_directory(self, school_id: uuid.UUID) -> list[dict]:
        from collections import defaultdict

        from app.db.models.academic import Class, Subject, TeacherSubjectMapping

        staff_roles = (
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.CLASS_INCHARGE,
            UserRole.TEACHER,
            UserRole.OPERATIONS,
        )
        users = (
            (
                await self.db.execute(
                    select(User)
                    .where(
                        User.school_id == school_id,
                        User.role.in_(staff_roles),
                        User.is_active.is_(True),
                    )
                    .order_by(User.full_name)
                )
            )
            .scalars()
            .all()
        )
        if not users:
            return []

        user_ids = [u.id for u in users]
        profile_rows = (
            (
                await self.db.execute(
                    select(StaffProfile).where(
                        StaffProfile.school_id == school_id,
                        StaffProfile.user_id.in_(user_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        profile_map = {p.user_id: p for p in profile_rows}

        teacher_rows = (
            (
                await self.db.execute(
                    select(Teacher).where(
                        Teacher.school_id == school_id,
                        Teacher.user_id.in_(user_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        teacher_map = {t.user_id: t for t in teacher_rows}

        incharge_rows = (
            await self.db.execute(
                select(Class.class_incharge_id, Class.grade, Class.section).where(
                    Class.school_id == school_id,
                    Class.class_incharge_id.isnot(None),
                )
            )
        ).all()
        incharge_map: dict[uuid.UUID, str] = {}
        for uid, grade, section in incharge_rows:
            if uid:
                incharge_map[uid] = f"{grade} {section}".strip()

        mapping_rows = (
            await self.db.execute(
                select(
                    TeacherSubjectMapping.teacher_id,
                    Subject.name,
                    Class.grade,
                    Class.section,
                )
                .join(Subject, Subject.id == TeacherSubjectMapping.subject_id)
                .join(Class, Class.id == TeacherSubjectMapping.class_id)
                .where(
                    TeacherSubjectMapping.school_id == school_id,
                    TeacherSubjectMapping.teacher_id.in_(user_ids),
                )
            )
        ).all()
        teacher_subjects: dict[uuid.UUID, list[str]] = defaultdict(list)
        teacher_grades: dict[uuid.UUID, set[str]] = defaultdict(set)
        for tid, subject_name, grade, section in mapping_rows:
            if subject_name and subject_name not in teacher_subjects[tid]:
                teacher_subjects[tid].append(subject_name)
            teacher_grades[tid].add(grade)

        dept_map = {
            UserRole.SUPER_ADMIN.value: "Administration",
            UserRole.ADMIN.value: "Administration",
            UserRole.CLASS_INCHARGE.value: "Academics",
            UserRole.TEACHER.value: "Academics",
            UserRole.OPERATIONS.value: "Operations",
        }
        role_labels = {
            UserRole.SUPER_ADMIN.value: "Principal",
            UserRole.ADMIN.value: "Admin",
            UserRole.CLASS_INCHARGE.value: "Class Incharge",
            UserRole.TEACHER.value: "Class Teacher",
            UserRole.OPERATIONS.value: "Operations",
        }
        category_role = {
            "admin": "Admin",
            "homeroom": "Homeroom",
            "subject_teacher": "Subject Teacher",
            "operations": "Operations",
        }

        def experience_label(profile: StaffProfile | None, teacher: Teacher | None) -> str | None:
            if profile and profile.previous_experience:
                text = profile.previous_experience.strip()
                if text:
                    return text if "year" in text.lower() else f"{text} years teaching"
            joining = None
            if profile and profile.joining_date:
                joining = profile.joining_date
            elif teacher and teacher.joining_date:
                joining = teacher.joining_date
            if joining:
                years = max(0, (date.today() - joining).days // 365)
                if years > 0:
                    return f"{years} years teaching"
            return None

        def classes_label(
            uid: uuid.UUID,
            staff_category: str,
            homeroom_class: str | None,
            grades: set[str],
        ) -> str:
            if staff_category == "admin":
                return "All Grades"
            if staff_category == "homeroom" and homeroom_class:
                return homeroom_class.split()[0] if homeroom_class else homeroom_class
            if grades:
                ordered = sorted(grades, key=lambda g: (len(g), g))
                if len(ordered) <= 3:
                    return ", ".join(ordered)
                return f"{', '.join(ordered[:3])} +{len(ordered) - 3}"
            if homeroom_class:
                return homeroom_class
            return "—"

        result: list[dict] = []
        for u in users:
            role_key = u.role.value
            cls = incharge_map.get(u.id)
            position = role_labels.get(role_key, role_key.replace("_", " ").title())
            if cls and role_key in (UserRole.TEACHER.value, UserRole.CLASS_INCHARGE.value):
                position = f"Class Teacher · {cls}"
            if role_key in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value):
                staff_category = "admin"
            elif role_key == UserRole.CLASS_INCHARGE.value or cls:
                staff_category = "homeroom"
            elif role_key == UserRole.TEACHER.value:
                staff_category = "subject_teacher"
            elif role_key == UserRole.OPERATIONS.value:
                staff_category = "operations"
            else:
                staff_category = "admin"

            profile = profile_map.get(u.id)
            teacher = teacher_map.get(u.id)
            employee_id = None
            if profile and profile.employee_id:
                employee_id = profile.employee_id
            elif teacher and teacher.employee_id:
                employee_id = teacher.employee_id

            subjects = teacher_subjects.get(u.id, [])
            subject = subjects[0] if subjects else None
            if not subject and profile and profile.department:
                subject = profile.department
            if not subject:
                subject = dept_map.get(role_key, "General")

            exp = experience_label(profile, teacher)
            meta_parts = [p for p in [employee_id, exp] if p]
            result.append(
                {
                    "id": str(u.id),
                    "name": u.full_name,
                    "role": position,
                    "department": dept_map.get(role_key, "Administration"),
                    "email": u.email,
                    "mobile": u.mobile,
                    "staff_category": staff_category,
                    "employee_id": employee_id,
                    "experience": exp,
                    "subtitle": " · ".join(meta_parts) if meta_parts else None,
                    "subject": subject,
                    "role_label": category_role.get(staff_category, "Staff"),
                    "classes": classes_label(
                        u.id,
                        staff_category,
                        cls,
                        teacher_grades.get(u.id, set()),
                    ),
                }
            )
        return result

    async def list_parents_directory(self, school_id: uuid.UUID) -> list[dict]:
        from app.db.models.student import Parent, Student, StudentParentMap

        rows = (
            await self.db.execute(
                select(Parent, User)
                .join(User, User.id == Parent.user_id)
                .where(Parent.school_id == school_id, User.is_active.is_(True))
                .order_by(User.full_name)
            )
        ).all()
        if not rows:
            return []

        parent_ids = [p.id for p, _ in rows]
        child_rows = (
            await self.db.execute(
                select(StudentParentMap, Student, User)
                .join(Student, Student.id == StudentParentMap.student_id)
                .join(User, User.id == Student.user_id)
                .where(StudentParentMap.parent_id.in_(parent_ids))
                .order_by(StudentParentMap.is_primary.desc(), StudentParentMap.created_at)
            )
        ).all()
        children_map: dict[uuid.UUID, list[str]] = {}
        # DM-2c: relationship lives on the link. The directory shows one line
        # per parent, so we surface the primary link's relationship (first row
        # per parent thanks to the ORDER BY above).
        relationship_map: dict[uuid.UUID, str] = {}
        for link, _student, student_user in child_rows:
            children_map.setdefault(link.parent_id, []).append(student_user.full_name)
            relationship_map.setdefault(link.parent_id, link.relationship_type.value)

        result: list[dict] = []
        for parent, user in rows:
            kids = children_map.get(parent.id, [])
            result.append(
                {
                    "id": str(parent.id),
                    "user_id": str(user.id),
                    "name": user.full_name,
                    "email": user.email,
                    "mobile": user.mobile,
                    "relationship": relationship_map.get(parent.id, "guardian"),
                    "children": kids,
                    "child_label": ", ".join(kids) if kids else "No linked students",
                }
            )
        return result
