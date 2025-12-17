-- =============================================
-- Unified SQLite Schema for Attendance System
-- =============================================
-- This schema is shared between Python core and TypeScript API
-- All tables use consistent data types and foreign key relationships

PRAGMA foreign_keys = ON;

-- =============================================
-- CORE TABLES
-- =============================================

-- Users table for authentication and authorization
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob TEXT,
    role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('admin', 'teacher', 'parent', 'student')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Classes/Courses table
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    teacher_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Students table (uses TEXT id for flexibility with external IDs)
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- RELATIONSHIP TABLES
-- =============================================

-- Parent-Student relationship (many-to-many)
CREATE TABLE IF NOT EXISTS parent_student (
    parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (parent_id, student_id)
);

-- =============================================
-- ATTENDANCE TABLES
-- =============================================

-- Class schedule (defines session times)
CREATE TABLE IF NOT EXISTS class_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_number INTEGER NOT NULL UNIQUE,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL
);

-- Semester configuration
CREATE TABLE IF NOT EXISTS semester_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Attendance sessions (main attendance records)
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
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
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Student circumstances (excuses, special conditions)
CREATE TABLE IF NOT EXISTS student_circumstances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    circumstance_type TEXT NOT NULL,
    description TEXT,
    start_date TEXT,
    end_date TEXT,
    session_numbers TEXT,  -- Comma-separated: '1,3,5' or 'all'
    excuse_type TEXT CHECK(excuse_type IN ('full', 'partial', 'late_arrival')),
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- COMMUNICATION TABLES
-- =============================================

-- Tickets for parent-teacher communication
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    type TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- FACE RECOGNITION TABLES
-- =============================================

-- Unregistered faces (pending assignment to students)
CREATE TABLE IF NOT EXISTS unregistered_faces (
    face_id TEXT PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- ANALYTICS TABLES
-- =============================================

-- Daily attendance insights (for reporting)
CREATE TABLE IF NOT EXISTS student_daily_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    student_name TEXT,
    sessions_attended INTEGER DEFAULT 0,
    sessions_late INTEGER DEFAULT 0,
    full_day_absent INTEGER DEFAULT 0,
    has_circumstances INTEGER DEFAULT 0,
    priority_score INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Agent analysis log (for AI-driven insights)
CREATE TABLE IF NOT EXISTS agent_analysis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_date TEXT NOT NULL,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    student_name TEXT,
    alert_level TEXT,
    reason TEXT,
    recommendation TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- INDEXES
-- =============================================

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Class indexes
CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id);

-- Student indexes
CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_id);
CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);

-- Attendance indexes
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_attendance_date_status ON attendance_sessions(session_date, attendance_status);
CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance_sessions(student_id, session_date);

-- Ticket indexes
CREATE INDEX IF NOT EXISTS idx_tickets_parent ON tickets(parent_id);
CREATE INDEX IF NOT EXISTS idx_tickets_teacher ON tickets(teacher_id);
CREATE INDEX IF NOT EXISTS idx_tickets_student ON tickets(student_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);

-- Circumstances indexes
CREATE INDEX IF NOT EXISTS idx_circumstances_student ON student_circumstances(student_id);
CREATE INDEX IF NOT EXISTS idx_circumstances_active ON student_circumstances(is_active);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_insights_date ON student_daily_insights(date);
CREATE INDEX IF NOT EXISTS idx_insights_student ON student_daily_insights(student_id);
CREATE INDEX IF NOT EXISTS idx_analysis_date ON agent_analysis_log(analysis_date);

-- =============================================
-- SEED DATA
-- =============================================

-- Insert class schedule (5 sessions per day)
INSERT OR IGNORE INTO class_schedule (session_number, start_time, end_time) VALUES
    (1, '07:20:00', '08:05:00'),
    (2, '08:10:00', '08:55:00'),
    (3, '09:00:00', '09:45:00'),
    (4, '09:55:00', '10:40:00'),
    (5, '10:45:00', '11:30:00');

-- Insert semester configuration
INSERT OR IGNORE INTO semester_config (semester_name, start_date, end_date, total_sessions, is_active) VALUES
    ('Fall 2024', '2024-09-01', '2024-12-20', 90, 1),
    ('Spring 2025', '2025-01-15', '2025-05-15', 85, 0);

-- Insert default class
INSERT OR IGNORE INTO classes (id, name) VALUES (1, 'Default Class');

-- Insert sample students
INSERT OR IGNORE INTO students (id, name, first_name, last_name, class_id) VALUES
    ('1', 'John Smith', 'John', 'Smith', 1),
    ('2', 'Emily Johnson', 'Emily', 'Johnson', 1),
    ('3', 'Michael Brown', 'Michael', 'Brown', 1),
    ('4', 'Sarah Davis', 'Sarah', 'Davis', 1),
    ('5', 'David Wilson', 'David', 'Wilson', 1),
    ('6', 'Jennifer Miller', 'Jennifer', 'Miller', 1),
    ('7', 'Christopher Moore', 'Christopher', 'Moore', 1),
    ('8', 'Jessica Taylor', 'Jessica', 'Taylor', 1),
    ('9', 'Matthew Anderson', 'Matthew', 'Anderson', 1),
    ('10', 'Ashley Thomas', 'Ashley', 'Thomas', 1),
    ('11', 'James Jackson', 'James', 'Jackson', 1),
    ('12', 'Elizabeth White', 'Elizabeth', 'White', 1),
    ('13', 'Daniel Harris', 'Daniel', 'Harris', 1),
    ('14', 'Michelle Martin', 'Michelle', 'Martin', 1),
    ('15', 'Robert Thompson', 'Robert', 'Thompson', 1),
    ('16', 'Laura Garcia', 'Laura', 'Garcia', 1),
    ('17', 'William Martinez', 'William', 'Martinez', 1),
    ('18', 'Amanda Robinson', 'Amanda', 'Robinson', 1),
    ('19', 'Joseph Clark', 'Joseph', 'Clark', 1),
    ('20', 'Stephanie Rodriguez', 'Stephanie', 'Rodriguez', 1),
    ('21', 'Thomas Lewis', 'Thomas', 'Lewis', 1),
    ('22', 'Rebecca Lee', 'Rebecca', 'Lee', 1),
    ('23', 'Charles Walker', 'Charles', 'Walker', 1),
    ('24', 'Patricia Hall', 'Patricia', 'Hall', 1),
    ('25', 'Mark Allen', 'Mark', 'Allen', 1),
    ('26', 'Linda Young', 'Linda', 'Young', 1),
    ('27', 'Donald King', 'Donald', 'King', 1),
    ('28', 'Barbara Wright', 'Barbara', 'Wright', 1),
    ('29', 'Steven Scott', 'Steven', 'Scott', 1),
    ('30', 'Margaret Green', 'Margaret', 'Green', 1),
    ('31', 'Paul Baker', 'Paul', 'Baker', 1),
    ('32', 'Nancy Adams', 'Nancy', 'Adams', 1),
    ('33', 'George Nelson', 'George', 'Nelson', 1),
    ('34', 'Betty Hill', 'Betty', 'Hill', 1),
    ('35', 'Kenneth Ramirez', 'Kenneth', 'Ramirez', 1),
    ('36', 'Dorothy Campbell', 'Dorothy', 'Campbell', 1),
    ('37', 'Edward Mitchell', 'Edward', 'Mitchell', 1),
    ('38', 'Helen Roberts', 'Helen', 'Roberts', 1),
    ('39', 'Brian Carter', 'Brian', 'Carter', 1),
    ('40', 'Deborah Phillips', 'Deborah', 'Phillips', 1),
    ('41', 'Ronald Evans', 'Ronald', 'Evans', 1),
    ('42', 'Sharon Turner', 'Sharon', 'Turner', 1),
    ('43', 'Jason Torres', 'Jason', 'Torres', 1),
    ('44', 'Carol Parker', 'Carol', 'Parker', 1),
    ('45', 'Kevin Collins', 'Kevin', 'Collins', 1),
    ('46', 'Ruth Edwards', 'Ruth', 'Edwards', 1),
    ('47', 'Timothy Stewart', 'Timothy', 'Stewart', 1),
    ('48', 'Anna Flores', 'Anna', 'Flores', 1),
    ('49', 'Brian Morris', 'Brian', 'Morris', 1),
    ('50', 'Catherine Nguyen', 'Catherine', 'Nguyen', 1);

-- Insert sample student circumstances
INSERT OR IGNORE INTO student_circumstances (student_id, circumstance_type, description, start_date, end_date, session_numbers, excuse_type) VALUES
    ('1', 'transportation', 'Bus route often runs late in morning traffic', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
    ('3', 'medical', 'Weekly allergy shots on Tuesday mornings', '2024-09-01', '2024-11-15', '1,2', 'late_arrival'),
    ('5', 'transportation', 'Parent works early shift, sometimes late dropping off', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
    ('7', 'family', 'Responsible for walking younger sibling to school', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
    ('12', 'extracurricular', 'Basketball practice until 6pm, sometimes oversleeps', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
    ('15', 'medical', 'Physical therapy for soccer injury twice a week', '2024-09-01', '2024-10-31', '3,5', 'partial'),
    ('18', 'transportation', 'Relies on city bus with inconsistent schedule', '2024-09-01', '2024-12-20', 'all', 'late_arrival'),
    ('22', 'family', 'Helps get younger siblings ready for school', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
    ('25', 'medical', 'Asthma condition, needs extra time between classes', '2024-09-01', '2024-12-20', 'all', 'late_arrival'),
    ('30', 'transportation', 'Bikes to school, affected by weather', '2024-09-01', '2024-12-20', 'all', 'late_arrival');

-- =============================================
-- VERIFICATION
-- =============================================

SELECT '✅ Database schema initialized successfully!' as status;
SELECT 'Tables created: ' || COUNT(*) as info FROM sqlite_master WHERE type='table';
SELECT 'Indexes created: ' || COUNT(*) as info FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';
SELECT 'Students: ' || COUNT(*) as info FROM students;