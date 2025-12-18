/**
 * Centralized configuration for the API
 */

// Python Face Recognition API
export const PYTHON_API_URL =
  process.env.PYTHON_API_URL || "http://localhost:8000";

// Database paths - unified database (Python attendance.db)
// All tables are now in a single database
export const ATTENDANCE_DB_PATHS = [
  "../face-reidentification/database/attendance.db",
  "face-reidentification/database/attendance.db",
  "../../face-reidentification/database/attendance.db",
  "../database/attendance.db",
  "database/attendance.db",
];

// JWT Configuration
const jwtSecret = process.env.JWT_SECRET;

if (!jwtSecret) {
  console.error("FATAL ERROR: JWT_SECRET is not defined in .env");
  process.exit(1);
}

export const JWT_SECRET: string = jwtSecret;

// Attendance status values (matching Python DB schema)
export const ATTENDANCE_STATUSES = [
  "on_time",
  "late",
  "absent",
  "excused",
  "left_early",
] as const;

export type AttendanceStatus = (typeof ATTENDANCE_STATUSES)[number];

// Session configuration
export const TOTAL_SESSIONS_PER_DAY = 5;

// User roles
export const USER_ROLES = ["admin", "teacher", "parent", "student"] as const;

export type UserRole = (typeof USER_ROLES)[number];
