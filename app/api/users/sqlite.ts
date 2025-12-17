import { Database } from "bun:sqlite";
import { existsSync } from "fs";

// Database paths - try multiple locations to find the Python attendance DB
const ATTENDANCE_DB_PATHS = [
  "../face-reidentification/database/attendance.db",
  "face-reidentification/database/attendance.db",
  "../../face-reidentification/database/attendance.db",
];

function resolveDbPath(): string {
  for (const p of ATTENDANCE_DB_PATHS) {
    if (existsSync(p)) {
      console.log(`📁 Connected to database at: ${p}`);
      return p;
    }
  }
  // Default fallback - will create new DB if not found
  console.warn("⚠️ Could not find Python attendance DB, creating new database");
  return "attendance.db";
}

const dbPath = resolveDbPath();
const db = new Database(dbPath, { create: true });

// Enable WAL mode for better performance
db.run("PRAGMA journal_mode = WAL;");
db.run("PRAGMA foreign_keys = ON;");

// Create users table if it doesn't exist (matches Python schema)
db.run(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob TEXT,
    role TEXT CHECK(role IN ('admin', 'teacher', 'parent', 'student')) NOT NULL DEFAULT 'student',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  );
`);

// Create classes table
db.run(`
  CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    teacher_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id)
  );
`);

// Create students table (matches Python schema with TEXT id)
db.run(`
  CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    class_id INTEGER,
    face_registered INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES classes(id)
  );
`);

// Add face_registered column if it doesn't exist (for existing databases)
try {
  db.run("ALTER TABLE students ADD COLUMN face_registered INTEGER DEFAULT 0");
} catch (e) {
  // Column already exists, ignore
}

// Create parent_student relationship table
db.run(`
  CREATE TABLE IF NOT EXISTS parent_student (
    parent_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (parent_id, student_id),
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
  );
`);

// Create tickets table
db.run(`
  CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    teacher_id INTEGER,
    class_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    type TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (class_id) REFERENCES classes(id)
  );
`);

// Create unregistered_faces table
db.run(`
  CREATE TABLE IF NOT EXISTS unregistered_faces (
    face_id TEXT PRIMARY KEY,
    class_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES classes(id)
  );
`);

// Create attendance_sessions table (matches Python schema)
db.run(`
  CREATE TABLE IF NOT EXISTS attendance_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    session_date TEXT NOT NULL,
    session_number INTEGER,
    entry_time TEXT,
    exit_time TEXT,
    duration_minutes INTEGER,
    status TEXT DEFAULT 'present' CHECK(status IN ('present', 'left')),
    attendance_status TEXT DEFAULT 'on_time' CHECK(attendance_status IN ('on_time', 'late', 'absent', 'excused', 'left_early')),
    late_minutes INTEGER DEFAULT 0,
    attendance_score REAL,
    reason_for_scoring TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
  );
`);

// Create indexes for attendance_sessions
db.run(
  "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance_sessions(student_id);",
);
db.run(
  "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_sessions(session_date);",
);
db.run(
  "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance_sessions(student_id, session_date);",
);

export { db, dbPath };
