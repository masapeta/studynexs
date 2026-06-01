"""School profile + academic-year schemas."""
from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class SchoolProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    tenant_slug: str
    board: str | None = None
    address: dict | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    theme_color: str | None = None
    enabled_modules: dict | None = None


class SchoolProfileUpdate(BaseModel):
    name: str | None = None
    board: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: dict | None = None
    logo_url: str | None = None
    theme_color: str | None = None
    enabled_modules: dict | None = None


class AcademicYearOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    year_label: str
    start_date: date
    end_date: date
    is_active: bool


class AcademicYearCreate(BaseModel):
    year_label: str
    start_date: date
    end_date: date
    is_active: bool = False
