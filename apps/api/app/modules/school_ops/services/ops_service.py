"""School operations service — library, events."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.school_ops import Event, LibraryBook, LibraryIssue, LibraryIssueStatus
from app.modules.school_ops.schemas.ops import EventCreate, LibraryBookCreate


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
