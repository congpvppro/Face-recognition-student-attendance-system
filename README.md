# Live Facial Recognition Attendance System

This project is a comprehensive student attendance system that uses live facial recognition, providing a seamless and modern experience for administrators, teachers, and students.

## Running

<b>Prerequisite:</b> [Bun](https://bun.com/) installed.


- Run web-app at `/app` with:
```
bun run dev
```
(Install dependencies first, with `bun install`)

- Run python core at `face-reidentification` with:
```
uvicorn api:app --host 0.0.0.0 --port 8000
```

## System Architecture

The system is built on a high-performance tech stack designed for a smooth user experience:

-   **Backend**: A fast and reliable API built with **Elysia** and **Bun**.
-   **Frontend**: A modern, interactive web application powered by **SvelteKit**.
-   **Face Recognition**: A powerful and accurate Python service that handles all the facial recognition tasks.

## Web Endpoints & User Roles

The application is divided into two main areas, each with distinct roles and functionalities.

### 1. The Public Kiosk (`/attendance`)

This is the primary interface for students. It's a single, dynamic page that operates in two modes, controlled by an administrator. Students **never** need to log in; they simply interact with the kiosk using their face.

-   **/attendance (Attendance Mode)**: This is the default mode. The screen displays a live camera feed. When a student looks at the camera, the system recognizes them, displays a "Welcome!" message, and automatically records their attendance for the day.

-   **/attendance (Registration Mode)**: An administrator can switch the kiosk to this mode for a specific class. Students from that class can then present their face to the camera one by one to be registered with the system.

### 2. The Management Portal (`/admin`)

This is a secure, login-protected area for staff to manage the system.

-   **/login**: The entry point for administrators and teachers to access the management portal.

-   **/admin/teachers**: (Admin only) On this page, an administrator can:
    -   Create new teacher accounts.
    -   View a list of all existing teachers in the system.

-   **/admin/classes**: (Admin only) This page allows an administrator to:
    -   Create new classes (e.g., "Grade 10 - Physics").
    -   Assign a teacher to each class.
    -   View a list of all classes, their assigned teachers, and the students enrolled in each.

-   **/admin/students**: (Admin or Teacher) This page is for managing student rosters. Staff can:
    -   Manually add new students to a class.
    -   View a list of all students currently in the system.

-   **/admin/unregistered**: (Admin or Teacher) This is the core of the registration workflow. After a registration session at the kiosk, all newly captured faces appear here. A teacher or admin can then:
    -   View the gallery of unregistered faces for their class.
    -   Assign each face to an existing student in the roster.
    -   Create a new student record and assign the face simultaneously.

-   **/admin/statistics**: (Admin or Teacher) This page provides a comprehensive overview of attendance data. Teachers can:
    -   View a complete log of all attendance records.
    -   Filter the records by class and/or date.
    -   See a list of students who were marked absent for a selected class on a specific day.