# Goal Description

Implement a comprehensive Role-Based Access Control (RBAC) system for the Staff Web Portal to ensure users only see and interact with modules they have permission for. Additionally, add the ability for School Admins to update user roles directly from the User Management page.

## User Review Required

> [!IMPORTANT]
> Your last message got cut off: *"teachers should not have access to fee related, but"*. 
> Did you want to add something specific that teachers *should* have access to (e.g., viewing other teachers, curriculum, etc.)? Please clarify if there are any specific teacher privileges you had in mind!

## Proposed Changes

### Frontend Navigation & Layouts
We will introduce role-based filtering so users only see the sidebar items they have access to.

#### [MODIFY] `apps/staff-web/src/components/Sidebar.tsx`
- Add a `roles` array to each navigation item definition.
- Update the rendering loop to only show items where `item.roles.includes(user.role)`.
- Nav Mapping:
  - **Dashboard & Attendance**: All roles
  - **Students**: All roles (Backend will filter to only show mapped students for teachers)
  - **Fees**: `admin`, `super_admin`, `class_incharge`, `operations`
  - **Teachers**: `admin`, `super_admin`, `class_incharge`
  - **User Management & Settings**: `admin`, `super_admin`

#### [MODIFY] `apps/staff-web/src/app/(dashboard)/layout.tsx`
- Add a client-side layout guard to prevent direct URL access. If a `teacher` manually navigates to `/fees`, they will be redirected to `/dashboard`.

### Backend Data Filtering (Academic Service)
To ensure Teachers only see their own students, the API must enforce data-level RBAC:
- **Teacher-Student Mapping:** The `GET /api/v1/students` endpoint must automatically scope the returned list to *only* include students in classes where the requesting teacher is assigned a subject or is the class incharge.
- If a teacher does not teach Class 4B, no student from Class 4B will be returned in their API response.
- This requires joining `Subject` (where `teacher_id = current_user`) -> `Class` -> `Student` during the fetch.

### User Management Modals
We will build out the functional modals on the Users page to allow admins to manage roles.

#### [MODIFY] `apps/staff-web/src/app/(dashboard)/users/page.tsx`
- Build a "Role Update" modal that opens when clicking "Edit" on a user.
- Add a dropdown to select a new role (`teacher`, `class_incharge`, `operations`, `admin`).
- Wire it to the `api.users.update` backend endpoint.

## Verification Plan

### Manual Verification
1. I will log in as an **Admin** and verify I can see all tabs and update a user's role.
2. I will log in as a **Teacher** and verify that the "Fees", "User Management", and "Settings" tabs are completely hidden from the sidebar.
3. I will test directly navigating to a blocked URL (e.g., `/fees` as a Teacher) and ensure it correctly redirects.
