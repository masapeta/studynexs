"""Seed transport routes + student assignments for the demo, and enable the Transport
module on the demo school so it appears in the nav.

Run:  python scripts/seed_transport.py
Idempotent: skips route creation if any route exists; always ensures the module flag.
"""
from __future__ import annotations

import asyncio
import random

from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.db.models.school import School
from app.db.models.school_ops import StudentTransport, TransportRoute
from app.db.models.student import Student

random.seed(11)

ROUTES = [
    {"route_name": "Route 1 — Kukatpally", "vehicle_number": "TS09 AB 1234",
     "driver_name": "Ramesh Kumar", "driver_contact": "+919800012001",
     "stops": ["Kukatpally", "KPHB", "Miyapur"]},
    {"route_name": "Route 2 — Ameerpet", "vehicle_number": "TS09 CD 5678",
     "driver_name": "Suresh Rao", "driver_contact": "+919800012002",
     "stops": ["Ameerpet", "SR Nagar", "Punjagutta"]},
    {"route_name": "Route 3 — Dilsukhnagar", "vehicle_number": "TS09 EF 9012",
     "driver_name": "Venkat Reddy", "driver_contact": "+919800012003",
     "stops": ["Dilsukhnagar", "Kothapet", "LB Nagar"]},
]


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == "test"))
        ).scalar_one_or_none()
        if school is None:
            print("Demo school not found. Run seed_demo_ssc.py first.")
            return

        # Enable the Transport module for the demo school (always, idempotent).
        school.enabled_modules = {**(school.enabled_modules or {}), "transport": True}

        existing = await db.scalar(
            select(func.count()).select_from(TransportRoute).where(
                TransportRoute.school_id == school.id
            )
        )
        if existing:
            await db.commit()
            print(f"Routes already seeded (count={existing}); ensured Transport module ON.")
            return

        routes = []
        for rd in ROUTES:
            r = TransportRoute(school_id=school.id, is_active=True, **rd)
            db.add(r)
            routes.append(r)
        await db.flush()

        students = (
            await db.execute(select(Student).where(Student.school_id == school.id))
        ).scalars().all()
        n_assigned = 0
        for i, stu in enumerate(students):
            if i % 3 != 0:  # assign ~1/3 of students
                continue
            route = routes[i % len(routes)]
            stop = random.choice(route.stops)
            db.add(StudentTransport(
                school_id=school.id, student_id=stu.id, route_id=route.id, boarding_stop=stop,
            ))
            n_assigned += 1

        await db.commit()
        print(f"Seeded transport: routes={len(routes)} assignments={n_assigned} (module ON)")


if __name__ == "__main__":
    asyncio.run(main())
