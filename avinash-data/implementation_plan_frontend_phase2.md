# Frontend Development: Phase 2 Plan (Attendance & Finance)

This plan outlines the next phase of frontend development for the Academix admin portal. We will move away from placeholder data by fully implementing the **Attendance** and **Finance** modules, including necessary backend API extensions to support the admin dashboards.

## User Review Required

> [!IMPORTANT]
> To fully power the Dashboard and Finance pages, I need to add two new read-only endpoints to the backend `fees` module (`GET /fees/stats` and `GET /fees/recent`). Are you okay with me modifying the backend to support these frontend views?

> [!WARNING]
> The UI designs will follow the premium "Bento Box" aesthetic established on the main dashboard. Let me know if you have specific color or layout preferences for the Attendance marking grid.

## Proposed Changes

### Backend APIs (New Endpoints for Admin Views)
We need aggregate endpoints for the admin dashboards, as the current APIs are student-specific.

#### [MODIFY] `apps/api/app/modules/fees/endpoints/fee.py`
- Add `GET /stats`: Returns total collected, pending amounts, and this month's collections.
- Add `GET /recent`: Returns the latest 10 fee receipts across the school.

#### [MODIFY] `apps/api/app/modules/attendance/endpoints/attendance.py`
- Add `GET /school-summary`: Returns the total school-wide attendance percentage for the dashboard "Daily Overview".

---

### Frontend Modules

#### [MODIFY] `apps/admin-web/src/app/dashboard/attendance/page.tsx`
- **Design**: Create a dynamic split-view. The top/left section will contain Date and Class selectors. The main section will display a data table of students.
- **Functionality**: 
  - Fetch classes via `/api/v1/academic/classes`.
  - Fetch students for the selected class.
  - Fetch existing attendance records via `/api/v1/attendance/class/{id}`.
  - Implement a bulk-save button that submits the `BulkMarkRequest` to `/api/v1/attendance/mark`.
- **Aesthetics**: Use toggle buttons (Present/Absent/Late) with smooth color transitions (Green/Red/Orange).

#### [MODIFY] `apps/admin-web/src/app/dashboard/finance/page.tsx`
- **Design**: Retain the premium 3-card summary layout but replace hardcoded numbers with state variables.
- **Functionality**: 
  - Fetch data from the new `/api/v1/fees/stats` and `/api/v1/fees/recent` endpoints.
  - Implement dynamic rendering of the "Recent Payments" table.

#### [MODIFY] `apps/admin-web/src/app/dashboard/page.tsx`
- **Functionality**: Connect the "Daily Overview" card to the new backend endpoints to show real School Attendance % and real Pending Fees.
- **UI Polish**: Ensure loading states use skeleton loaders instead of jarring spinners to maintain the premium feel.

## Verification Plan

### Manual Verification
1. **Attendance Flow**: I will navigate to the Attendance page, select a class, mark several students as Absent/Late, save, and verify the data persists upon page reload.
2. **Finance Data**: I will verify that the Finance page accurately reflects the total fees in the database.
3. **Dashboard Metrics**: I will verify the main dashboard numbers perfectly match the detailed module pages.
