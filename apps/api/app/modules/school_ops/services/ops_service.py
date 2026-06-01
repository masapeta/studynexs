"""School operations service — library, events."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.residential import BlockGender, ResidentialBlock, RoomAllocation
from app.db.models.school_ops import (
    Event,
    LibraryBook,
    LibraryIssue,
    LibraryIssueStatus,
    StudentTransport,
    TransportRoute,
)
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.school_ops.schemas.ops import (
    EventCreate,
    LibraryBookCreate,
    ResidentialAllocateRequest,
    ResidentialBlockCreate,
    TransportAssignRequest,
    TransportRouteCreate,
)


class SchoolOpsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Library ──────────────────────────────────────────────────

    async def list_books(self, school_id: uuid.UUID, search: str | None = None) -> list[LibraryBook]:
        query = select(LibraryBook).where(LibraryBook.school_id == school_id)
        if search:
            query = query.where(LibraryBook.title.ilike(f"%{search}%"))
        result = await self.db.execute(query.order_by(LibraryBook.title).limit(100))
        return list(result.scalars().all())

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

    async def issue_book(self, school_id: uuid.UUID, book_id: uuid.UUID, user_id: uuid.UUID) -> LibraryIssue:
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
            select(Event).where(Event.school_id == school_id).order_by(Event.event_date.desc()).limit(50)
        )
        return list(result.scalars().all())

    async def create_event(self, school_id: uuid.UUID, data: EventCreate, created_by: uuid.UUID) -> Event:
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
            await self.db.execute(
                select(TransportRoute)
                .where(TransportRoute.school_id == school_id)
                .order_by(TransportRoute.route_name)
            )
        ).scalars().all()
        route_ids = [r.id for r in routes]
        counts: dict = {}
        if route_ids:
            rows = (
                await self.db.execute(
                    select(StudentTransport.route_id, func.count())
                    .where(StudentTransport.route_id.in_(route_ids))
                    .group_by(StudentTransport.route_id)
                )
            ).all()
            counts = {rid: c for rid, c in rows}
        return [
            {
                "id": str(r.id), "route_name": r.route_name,
                "vehicle_number": r.vehicle_number, "driver_name": r.driver_name,
                "driver_contact": r.driver_contact, "stops": r.stops or [],
                "is_active": r.is_active, "student_count": counts.get(r.id, 0),
            }
            for r in routes
        ]

    async def create_route(
        self, school_id: uuid.UUID, data: TransportRouteCreate
    ) -> TransportRoute:
        route = TransportRoute(
            school_id=school_id, route_name=data.route_name,
            vehicle_number=data.vehicle_number, driver_name=data.driver_name,
            driver_contact=data.driver_contact, stops=data.stops or [],
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
            {"student_id": str(st.student_id), "name": name,
             "admission_no": adm, "boarding_stop": st.boarding_stop}
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
                select(Student).where(
                    Student.id == data.student_id, Student.school_id == school_id
                )
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
            student_id=data.student_id, route_id=data.route_id,
            boarding_stop=data.boarding_stop,
        )
        self.db.add(st)
        await self.db.flush()
        return st

    # ── Residential ──────────────────────────────────────────────

    async def list_residential_blocks(self, school_id: uuid.UUID) -> list[dict]:
        blocks = (
            await self.db.execute(
                select(ResidentialBlock)
                .where(ResidentialBlock.school_id == school_id)
                .order_by(ResidentialBlock.block_name)
            )
        ).scalars().all()
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
                "id": str(b.id), "block_name": b.block_name,
                "block_gender": b.block_gender.value if b.block_gender else "mixed",
                "warden_name": b.warden_name, "warden_contact": b.warden_contact,
                "total_rooms": b.total_rooms, "is_active": b.is_active,
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
            school_id=school_id, block_name=data.block_name, block_gender=gender,
            warden_name=data.warden_name, warden_contact=data.warden_contact,
            total_rooms=data.total_rooms,
        )
        self.db.add(block)
        await self.db.flush()
        return block

    async def list_block_residents(
        self, school_id: uuid.UUID, block_id: uuid.UUID
    ) -> list[dict]:
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
            {"student_id": str(a.student_id), "name": name,
             "admission_no": adm, "room_number": a.room_number}
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
                select(Student).where(
                    Student.id == data.student_id, Student.school_id == school_id
                )
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
            school_id=school_id, student_id=data.student_id,
            block_id=data.block_id, room_number=data.room_number,
        )
        self.db.add(alloc)
        await self.db.flush()
        return alloc
