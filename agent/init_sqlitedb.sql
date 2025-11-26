-- SQLite-compatible schema for attendance system
-- =============================================

-- Create tables
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    session_date TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    duration_minutes INTEGER,
    status TEXT DEFAULT 'present' CHECK(status IN ('present', 'left')),
    attendance_status TEXT DEFAULT 'on_time' CHECK(attendance_status IN ('on_time', 'late', 'absent', 'excused', 'left_early')),
    late_minutes INTEGER DEFAULT 0,
    reason_for_scoring TEXT,
    session_number INTEGER,
    attendance_score REAL,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE IF NOT EXISTS daily_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_minutes INTEGER DEFAULT 0,
    first_entry TEXT,
    last_exit TEXT,
    current_status TEXT DEFAULT 'absent' CHECK(current_status IN ('present', 'absent')),
    attendance_status TEXT DEFAULT 'absent' CHECK(attendance_status IN ('on_time', 'late', 'absent', 'excused')),
    late_minutes INTEGER DEFAULT 0,
    attendance_score REAL DEFAULT 0,
    FOREIGN KEY (student_id) REFERENCES students(id),
    UNIQUE (student_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS class_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_number INTEGER NOT NULL UNIQUE,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS semester_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- UPDATED: Student circumstances with session-specific excuses
CREATE TABLE IF NOT EXISTS student_circumstances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    circumstance_type TEXT NOT NULL,
    description TEXT,
    start_date TEXT,
    end_date TEXT,
    -- NEW: Session-specific excuses
    session_numbers TEXT, -- Comma-separated session numbers: '1,3,5' or 'all' for all sessions
    excuse_type TEXT CHECK(excuse_type IN ('full', 'partial', 'late_arrival')),
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students (id)
);

-- Create index (from your original)
CREATE INDEX IF NOT EXISTS idx_date_status ON attendance_sessions (session_date, status);

-- Insert class schedule (YOUR ORIGINAL TIMES)
INSERT OR IGNORE INTO class_schedule (session_number, start_time, end_time) VALUES
(1, '07:20:00', '08:05:00'),
(2, '08:10:00', '08:55:00'),
(3, '09:00:00', '09:45:00'),
(4, '09:55:00', '10:40:00'),
(5, '10:45:00', '11:30:00');

-- Insert semester configuration
INSERT OR IGNORE INTO semester_config (semester_name, start_date, end_date, total_sessions, is_active) VALUES
('Fall 2024', '2024-09-01', '2024-12-20', 90, 1),
('Spring 2024', '2024-01-15', '2024-05-15', 85, 0);

-- Insert ALL 100 students (YOUR ORIGINAL LIST)
INSERT OR IGNORE INTO students (name) VALUES
('John Smith'),('Emily Johnson'),('Michael Brown'),('Sarah Davis'),('David Wilson'),
('Jennifer Miller'),('Christopher Moore'),('Jessica Taylor'),('Matthew Anderson'),('Ashley Thomas'),
('James Jackson'),('Elizabeth White'),('Daniel Harris'),('Michelle Martin'),('Robert Thompson'),
('Laura Garcia'),('William Martinez'),('Amanda Robinson'),('Joseph Clark'),('Stephanie Rodriguez'),
('Thomas Lewis'),('Rebecca Lee'),('Charles Walker'),('Patricia Hall'),('Mark Allen'),
('Linda Young'),('Donald King'),('Barbara Wright'),('Steven Scott'),('Margaret Green'),
('Paul Baker'),('Nancy Adams'),('George Nelson'),('Betty Hill'),('Kenneth Ramirez'),
('Dorothy Campbell'),('Edward Mitchell'),('Helen Roberts'),('Brian Carter'),('Deborah Phillips'),
('Ronald Evans'),('Sharon Turner'),('Jason Torres'),('Carol Parker'),('Kevin Collins'),
('Ruth Edwards'),('Timothy Stewart'),('Anna Flores'),('Brian Morris'),('Catherine Nguyen'),
('Steven Murphy'),('Pamela Rivera'),('Jeffrey Cook'),('Martha Rogers'),('Frank Morgan'),
('Teresa Peterson'),('Gary Cooper'),('Carolyn Reed'),('Larry Bailey'),('Jacqueline Bell'),
('Scott Kelly'),('Diane Howard'),('Eric Ward'),('Janet Cox'),('Stephen Diaz'),
('Heather Richardson'),('Raymond Wood'),('Emma Watson'),('Patrick Brooks'),('Christine Sanders'),
('Gregory Price'),('Rachel Bennett'),('Jeremy Barnes'),('Victoria Fisher'),('Dennis Henderson'),
('Judith Coleman'),('Walter Gray'),('Brenda James'),('Harold Reyes'),('Megan Hughes'),
('Arthur Foster'),('Cheryl Butler'),('Zachary Simmons'),('Evelyn Russell'),('Henry Griffin'),
('Joan Diaz'),('Carl Hayes'),('Andrea Myers'),('Jack Ford'),('Rose Hamilton'),
('Tyler Graham'),('Nicole Sullivan'),('Aaron Wallace'),('Katherine Woods'),('Billy Cole'),
('Lori West'),('Bruce Jordan'),('Diana Owens'),('Ethan Reynolds'),('Marie Fisher');

-- UPDATED: Insert student circumstances with session-specific excuses
INSERT OR IGNORE INTO student_circumstances (student_id, circumstance_type, description, start_date, end_date, session_numbers, excuse_type) VALUES
(1, 'transportation', 'Bus route from north side often runs late in morning traffic', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(3, 'medical', 'Weekly allergy shots on Tuesday mornings', '2024-09-01', '2024-11-15', '1,2', 'late_arrival'),
(5, 'transportation', 'Parent works early shift, sometimes late dropping off', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(7, 'family', 'Responsible for walking younger sibling to elementary school', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(12, 'extracurricular', 'Basketball practice until 6pm, sometimes oversleeps', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(15, 'medical', 'Physical therapy for soccer injury twice a week', '2024-09-01', '2024-10-31', '3,5', 'partial'),
(18, 'transportation', 'Relies on city bus with inconsistent morning schedule', '2024-09-01', '2024-12-20', 'all', 'late_arrival'),
(22, 'family', 'Helps get younger siblings ready for school', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(25, 'medical', 'Asthma condition, needs extra time between classes', '2024-09-01', '2024-12-20', 'all', 'late_arrival'),
(30, 'transportation', 'Bikes to school, affected by rainy weather', '2024-09-01', '2024-12-20', 'all', 'late_arrival'),
(35, 'work', 'Weekend job at grocery store, sometimes affects Monday energy', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(42, 'family', 'Helps grandmother with morning medication before school', '2024-09-01', '2024-10-15', '1,2', 'late_arrival'),
(47, 'transportation', 'Carpool with neighbors, dependent on their schedule', '2024-09-01', '2024-12-20', 'all', 'late_arrival'),
(53, 'medical', 'ADHD medication adjustment period', '2024-09-01', '2024-10-15', '1', 'late_arrival'),
(58, 'work', 'Morning paper route before school', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(62, 'transportation', 'Family shares one car with multiple students', '2024-09-01', '2024-12-20', 'all', 'late_arrival'),
(67, 'family', 'Babysits neighbor''s kids until their parents leave for work', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(73, 'medical', 'New glasses prescription, adjusting to vision changes', '2024-09-01', '2024-10-31', '1,2', 'late_arrival'),
(78, 'transportation', 'Train to school from next town over', '2024-09-01', '2024-12-20', 'all', 'late_arrival'),
(85, 'extracurricular', 'Student council morning meetings run long sometimes', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(92, 'family', 'Helps at family coffee shop before school', '2024-09-01', '2024-12-20', '1', 'late_arrival'),
(97, 'medical', 'Recovering from broken leg, slower movement between classes', '2024-09-01', '2024-11-15', 'all', 'late_arrival'),
(8, 'extracurricular', 'Marching band practice before school on Fridays', '2024-09-01', '2024-12-20', '1', 'partial'),
(21, 'academic', 'Peer tutoring in math lab during 4th period', '2024-09-01', '2024-12-20', '4', 'partial'),
(34, 'medical', 'Orthodontist appointments monthly', '2024-09-01', '2024-12-20', '3,4', 'late_arrival'),
(45, 'family', 'Takes family dog to vet appointments monthly', '2024-09-01', '2024-12-20', '2,3', 'partial'),
(56, 'transportation', 'Learning to drive, parent supervision required', '2024-09-01', '2024-10-31', 'all', 'late_arrival'),
(68, 'academic', 'College application counseling during lunch period', '2024-09-01', '2024-11-30', '5', 'partial'),
(79, 'medical', 'Seasonal allergies during pollen season', '2024-03-01', '2024-05-31', 'all', 'late_arrival'),
(88, 'extracurricular', 'Science Olympiad team competitions monthly', '2024-09-01', '2024-12-20', '3,4,5', 'full'),
(99, 'family', 'Parent-teacher conference appointments', '2024-09-01', '2024-12-20', '2,3', 'partial');

-- Insert sample attendance data for last 7 days WITH session_number
INSERT OR IGNORE INTO attendance_sessions (student_id, session_date, entry_time, session_number, duration_minutes, attendance_status, late_minutes)
SELECT 
    s.id as student_id,
    date('now', '-' || (abs(random()) % 7) || ' days') as session_date,
    time('07:20:00', '+' || (abs(random()) % 45) || ' minutes') as entry_time,
    CASE 
        WHEN time('07:20:00', '+' || (abs(random()) % 45) || ' minutes') BETWEEN '07:20:00' AND '08:05:00' THEN 1
        WHEN time('07:20:00', '+' || (abs(random()) % 45) || ' minutes') BETWEEN '08:10:00' AND '08:55:00' THEN 2
        WHEN time('07:20:00', '+' || (abs(random()) % 45) || ' minutes') BETWEEN '09:00:00' AND '09:45:00' THEN 3
        WHEN time('07:20:00', '+' || (abs(random()) % 45) || ' minutes') BETWEEN '09:55:00' AND '10:40:00' THEN 4
        WHEN time('07:20:00', '+' || (abs(random()) % 45) || ' minutes') BETWEEN '10:45:00' AND '11:30:00' THEN 5
        ELSE 1
    END as session_number,
    abs(random()) % 20 + 40 as duration_minutes,
    CASE abs(random()) % 10
        WHEN 0 THEN 'absent'
        WHEN 1 THEN 'late'
        WHEN 2 THEN 'late'
        ELSE 'on_time'
    END as attendance_status,
    CASE 
        WHEN abs(random()) % 4 = 0 THEN abs(random()) % 30
        ELSE 0
    END as late_minutes
FROM students s
WHERE abs(random()) % 10 < 8
LIMIT 500;

-- Create daily attendance summaries
INSERT OR IGNORE INTO daily_attendance (student_id, attendance_date, total_sessions, total_minutes, attendance_status, late_minutes, attendance_score)
SELECT 
    student_id,
    session_date as attendance_date,
    COUNT(*) as total_sessions,
    SUM(duration_minutes) as total_minutes,
    CASE 
        WHEN SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END) > 0 THEN 'absent'
        WHEN SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) > 0 THEN 'late'
        ELSE 'on_time'
    END as attendance_status,
    SUM(late_minutes) as late_minutes,
    ROUND((COUNT(*) * 100.0 / 5), 2) as attendance_score
FROM attendance_sessions 
WHERE session_date >= date('now', '-7 days')
GROUP BY student_id, session_date;

-- Update current_status for today's attendance
UPDATE daily_attendance 
SET current_status = 'present'
WHERE attendance_date = date('now') 
AND total_sessions > 0;

UPDATE daily_attendance 
SET current_status = 'absent'
WHERE attendance_date = date('now') 
AND (total_sessions = 0 OR total_sessions IS NULL);

-- Print summary
SELECT '✅ Database initialized successfully!' as status;
SELECT 'Students: ' || COUNT(*) FROM students;
SELECT 'Student Circumstances: ' || COUNT(*) FROM student_circumstances;
SELECT 'Attendance sessions: ' || COUNT(*) FROM attendance_sessions;
SELECT 'Daily records: ' || COUNT(*) FROM daily_attendance;