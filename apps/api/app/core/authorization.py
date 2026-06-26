"""
Object-level authorization helpers — school scope and parent/student ownership.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.fee import StudentFeeRecord
from app.db.models.file import FileCategory, UploadedFile
from app.db.models.student import Parent, Student, StudentParentMap

# Roles that may access any non-identity file within their own school.
_STAFF_FILE_ROLES = ("admin", "super_admin", "operations", "teacher", "class_incharge")
# Admission identity documents (Aadhaar, birth certificate scans) — admin only.
# REPORT_CARD files are used for academic PDFs elsewhere; admission uploads use DOCUMENT.
_IDENTITY_DOC_ROLES = frozenset({"admin", "super_admin"})
_IDENTITY_DOC_CATEGORIES = frozenset({FileCategory.DOCUMENT})


async def get_student_in_school(
    db: AsyncSession, school_id: uuid.UUID, student_id: uuid.UUID
) -> Student | None:
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )
    return result.scalar_one_or_none()


async def parent_linked_to_student(
    db: AsyncSession, school_id: uuid.UUID, parent_user_id: uuid.UUID, student_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(StudentParentMap.id)
        .join(Parent, Parent.id == StudentParentMap.parent_id)
        .join(Student, Student.id == StudentParentMap.student_id)
        .where(
            Student.id == student_id,
            Student.school_id == school_id,
            Parent.user_id == parent_user_id,
            Parent.school_id == school_id,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def assert_can_access_student(
    current_user: CurrentUser, db: AsyncSession, student_id: uuid.UUID
) -> Student:
    """Admin/ops roles: school scope. Parent: linked child. Student: self only."""
    school_id = uuid.UUID(current_user.school_id)
    student = await get_student_in_school(db, school_id, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    if current_user.role in ("admin", "super_admin", "operations"):
        return student

    if current_user.role == "parent":
        if await parent_linked_to_student(
            db, school_id, uuid.UUID(current_user.id), student_id
        ):
            return student
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if current_user.role == "student":
        if str(student.user_id) == current_user.id:
            return student
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if current_user.role in ("teacher", "class_incharge"):
        from app.core.staff_permissions import get_staff_scope

        scope = await get_staff_scope(db, current_user)
        if not scope.is_class_incharge(student.class_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return student

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


async def assert_can_pay_fee(
    current_user: CurrentUser, db: AsyncSession, fee_record_id: uuid.UUID
) -> StudentFeeRecord:
    school_id = uuid.UUID(current_user.school_id)
    result = await db.execute(
        select(StudentFeeRecord).where(
            StudentFeeRecord.id == fee_record_id,
            StudentFeeRecord.school_id == school_id,
        )
    )
    fee_record = result.scalar_one_or_none()
    if not fee_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee record not found")

    if current_user.role in ("admin", "super_admin", "operations"):
        return fee_record

    if current_user.role == "parent":
        if await parent_linked_to_student(
            db, school_id, uuid.UUID(current_user.id), fee_record.student_id
        ):
            return fee_record
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to process payment",
    )


def assert_can_access_file(current_user: CurrentUser, record: UploadedFile) -> None:
    """Authorize a file download. The caller has already enforced school scope."""
    # SECURITY-REVIEW: identity document uploads are restricted to admissions admins.
    if record.category in _IDENTITY_DOC_CATEGORIES:
        if current_user.role not in _IDENTITY_DOC_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return

    if current_user.role in _STAFF_FILE_ROLES:
        return
    if str(record.uploaded_by) == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
