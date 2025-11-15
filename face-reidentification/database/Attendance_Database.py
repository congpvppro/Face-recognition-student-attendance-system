import sqlite3
from datetime import datetime
import datetime as dt
from contextlib import contextmanager
import logging
import os

class AttendanceDatabase:

    def __init__(self, db_path='attendance.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.connection = None
        self._init_database()

    def _init_database(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create students table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS attendance_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        session_date TEXT NOT NULL,
                        entry_time TEXT NOT NULL,
                        exit_time TEXT,
                        duration_minutes INTEGER,
                        status TEXT DEFAULT 'present' CHECK(status IN ('present', 'left')),
                        attendance_status TEXT DEFAULT 'on_time' CHECK(attendance_status IN ('on_time', 'late', 'absent')),
                        late_minutes INTEGER DEFAULT 0,
                        FOREIGN KEY (student_id) REFERENCES students(id)
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_status ON attendance_sessions (session_date, status)")


                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        attendance_date TEXT NOT NULL,
                        total_sessions INTEGER DEFAULT 0,
                        total_minutes INTEGER DEFAULT 0,
                        first_entry TEXT,
                        last_exit TEXT,
                        current_status TEXT DEFAULT 'absent' CHECK(current_status IN ('present', 'absent')),
                        attendance_status TEXT DEFAULT 'absent' CHECK(attendance_status IN ('on_time', 'late', 'absent')),
                        late_minutes INTEGER DEFAULT 0,
                        attendance_score REAL DEFAULT 0,
                        FOREIGN KEY (student_id) REFERENCES students(id),
                        UNIQUE (student_id, attendance_date)
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS class_schedule (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_number INTEGER NOT NULL UNIQUE,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL
                    )
                """)

                cursor.execute("SELECT COUNT(*) FROM class_schedule")
                if cursor.fetchone()[0] == 0:
                    schedule_data = [
                        (1, '07:20:00', '08:05:00'),
                        (2, '08:10:00', '08:55:00'),
                        (3, '09:00:00', '09:45:00'),
                        (4, '09:55:00', '10:40:00'),
                        (5, '10:45:00', '11:30:00')
                    ]
                    cursor.executemany("""
                        INSERT INTO class_schedule (session_number, start_time, end_time)
                        VALUES (?, ?, ?)
                    """, schedule_data)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS semester_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        semester_name TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        total_sessions INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.commit()
                logging.info("Database initialized successfully")

        except sqlite3.Error as e:
            logging.error(f"Error initializing database: {e}")
            raise

    def _str_to_time(self, time_str):
        if isinstance(time_str, str):
            return datetime.strptime(time_str, '%H:%M:%S').time()
        return time_str
        
    def get_current_session_time(self):
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                current_time = datetime.now().strftime('%H:%M:%S')

                cursor.execute("""
                    SELECT session_number, start_time, end_time 
                    FROM class_schedule
                    WHERE start_time <= ? AND end_time >= ?
                    ORDER BY start_time DESC
                    LIMIT 1
                """, (current_time, current_time))

                result = cursor.fetchone()

                if result:
                    return {
                        'session_number': result['session_number'],
                        'start_time': self._str_to_time(result['start_time']),
                        'end_time': self._str_to_time(result['end_time'])
                    }

                cursor.execute("""
                    SELECT session_number, start_time, end_time 
                    FROM class_schedule
                    WHERE start_time > ?
                    ORDER BY start_time ASC
                    LIMIT 1
                """, (current_time,))

                result = cursor.fetchone()
                
                if result:
                    return {
                        'session_number': result['session_number'],
                        'start_time': self._str_to_time(result['start_time']),
                        'end_time': self._str_to_time(result['end_time'])
                    }

                return None

        except sqlite3.Error as e:
            logging.error(f"Error getting current session: {e}")
            return None
            
    def calculate_late_minutes(self, entry_time, scheduled_start_time):
        if isinstance(entry_time, dt.datetime):
            entry_time = entry_time.time()

        entry_datetime = datetime.combine(datetime.today(), entry_time)
        scheduled_datetime = datetime.combine(datetime.today(), scheduled_start_time)

        if entry_datetime > scheduled_datetime:
            delta = entry_datetime - scheduled_datetime
            return int(delta.total_seconds() / 60)
        return 0
        
    @contextmanager
    def get_connection(self, row_factory=None):
        conn = sqlite3.connect(self.db_path)
        if row_factory:
            conn.row_factory = row_factory
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_or_create_student(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
                result = cursor.fetchone()

                if not result:
                    cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
                    student_id = cursor.lastrowid
                else:
                    student_id = result[0]

                return student_id
        except sqlite3.Error as e:
            logging.error(f"Error getting/creating student: {e}")
            return None

    def record_entry(self, name):
        try:
            student_id = self.get_or_create_student(name)
            if student_id is None:
                return None

            with self.get_connection() as conn:
                cursor = conn.cursor()

                current_datetime = datetime.now()
                current_date = current_datetime.strftime('%Y-%m-%d')
                current_time = current_datetime.time()

                session_info = self.get_current_session_time()

                if not session_info:
                    logging.warning("No active session found")
                    return None

                late_minutes = self.calculate_late_minutes(current_time, session_info['start_time'])

                if late_minutes > 0:
                    attendance_status = 'late'
                    attendance_score = 0.5
                    logging.warning(f"  {name} is LATE by {late_minutes} minutes!")
                    print(f"\n{'=' * 60}")
                    print(f"LATE ARRIVAL ALERT")
                    print(f"{'=' * 60}")
                    print(f"Student: {name}")
                    print(f"Scheduled: {session_info['start_time'].strftime('%H:%M')}")
                    print(f"Arrived: {current_time.strftime('%H:%M:%S')}")
                    print(f"Late by: {late_minutes} minutes")
                    print(f"Score: 0.5/1.0")
                    print(f"{'=' * 60}\n")
                else:
                    attendance_status = 'on_time'
                    attendance_score = 1.0
                    logging.info(f"✓ {name} arrived on time")

                cursor.execute("""
                    INSERT INTO attendance_sessions 
                    (student_id, session_date, entry_time, status, attendance_status, late_minutes)
                    VALUES (?, ?, ?, 'present', ?, ?)
                """, (student_id, current_date, current_datetime.strftime('%Y-%m-%d %H:%M:%S'), attendance_status, late_minutes))

                session_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO daily_attendance 
                    (student_id, attendance_date, total_sessions, first_entry, current_status, 
                     attendance_status, late_minutes, attendance_score)
                    VALUES (?, ?, 1, ?, 'present', ?, ?, ?)
                    ON CONFLICT(student_id, attendance_date) DO UPDATE SET
                        total_sessions = total_sessions + 1,
                        current_status = 'present',
                        first_entry = MIN(first_entry, excluded.first_entry),
                        attendance_status = CASE WHEN attendance_status = 'on_time' THEN attendance_status ELSE excluded.attendance_status END,
                        late_minutes = late_minutes + excluded.late_minutes,
                        attendance_score = attendance_score + excluded.attendance_score
                """, (student_id, current_date, current_datetime.strftime('%Y-%m-%d %H:%M:%S'), attendance_status, late_minutes, attendance_score))

                logging.info(f"Entry recorded for {name} at {current_datetime.strftime('%H:%M:%S')}")
                return session_id

        except sqlite3.Error as e:
            logging.error(f"Error recording entry: {e}")
            return None

    def record_exit(self, name):
        try:
            student_id = self.get_or_create_student(name)
            if student_id is None:
                return False

            with self.get_connection() as conn:
                cursor = conn.cursor()

                current_datetime = datetime.now()
                current_date = current_datetime.strftime('%Y-%m-%d')

                cursor.execute("""
                    SELECT id, entry_time FROM attendance_sessions
                    WHERE student_id = ? 
                    AND session_date = ? 
                    AND status = 'present'
                    ORDER BY entry_time DESC
                    LIMIT 1
                """, (student_id, current_date))

                result = cursor.fetchone()

                if result:
                    session_id, entry_time_str = result
                    entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S')
                    duration = int((current_datetime - entry_time).total_seconds() / 60)

                    cursor.execute("""
                        UPDATE attendance_sessions
                        SET exit_time = ?, duration_minutes = ?, status = 'left'
                        WHERE id = ?
                    """, (current_datetime.strftime('%Y-%m-%d %H:%M:%S'), duration, session_id))

                    cursor.execute("""
                        UPDATE daily_attendance
                        SET total_minutes = total_minutes + ?,
                            last_exit = ?,
                            current_status = 'absent'
                        WHERE student_id = ? AND attendance_date = ?
                    """, (duration, current_datetime.strftime('%Y-%m-%d %H:%M:%S'), student_id, current_date))

                    logging.info(
                        f" Exit recorded for {name} at {current_datetime.strftime('%H:%M:%S')} (Duration: {duration} min)")
                    return True
                else:
                    logging.warning(f"No open session found for {name}")
                    return False

        except sqlite3.Error as e:
            logging.error(f"Error recording exit: {e}")
            return False

    def get_current_status(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().strftime('%Y-%m-%d')

                cursor.execute("""
                    SELECT da.current_status
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE s.name = ? AND da.attendance_date = ?
                """, (name, current_date))

                result = cursor.fetchone()
                return result[0] if result else 'absent'

        except sqlite3.Error as e:
            logging.error(f"Error getting status: {e}")
            return 'absent'

    def get_daily_report(self, date=None):
        try:
            with self.get_connection(row_factory=sqlite3.Row) as conn:
                cursor = conn.cursor()
                target_date = date or datetime.now().strftime('%Y-%m-%d')

                cursor.execute("""
                    SELECT 
                        s.name,
                        da.total_sessions,
                        da.total_minutes,
                        da.first_entry,
                        da.last_exit,
                        da.current_status
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE da.attendance_date = ?
                    ORDER BY s.name
                """, (target_date,))

                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logging.error(f"Error getting daily report: {e}")
            return []

    def get_current_students(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().strftime('%Y-%m-%d')

                cursor.execute("""
                    SELECT s.name
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE da.attendance_date = ? AND da.current_status = 'present'
                    ORDER BY s.name
                """, (current_date,))

                return [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logging.error(f"Error getting current students: {e}")
            return []
    
    def get_absent_students(self, registered_students):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().strftime('%Y-%m-%d')

                cursor.execute("""
                    SELECT s.name
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE da.attendance_date = ?
                """, (current_date,))

                present_students = set([row[0] for row in cursor.fetchall()])
                absent_students = set(registered_students) - present_students
                return list(absent_students)

        except sqlite3.Error as e:
            logging.error(f"Error getting absent students: {e}")
            return []

    def mark_absent(self, name):
        try:
            student_id = self.get_or_create_student(name)
            if student_id is None:
                return False
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().strftime('%Y-%m-%d')

                cursor.execute("""
                    INSERT INTO daily_attendance 
                    (student_id, attendance_date, attendance_status, attendance_score, current_status)
                    VALUES (?, ?, 'absent', 0, 'absent')
                    ON CONFLICT(student_id, attendance_date) DO UPDATE SET
                        attendance_status = 'absent',
                        current_status = 'absent'
                """, (student_id, current_date))
                
                logging.info(f"Marked {name} as absent")
                return True

        except sqlite3.Error as e:
            logging.error(f"Error marking absent: {e}")
            return False

    def calculate_attendance_score(self, name, total_sessions_in_semester):
        try:
            student_id = self.get_or_create_student(name)
            if student_id is None:
                return 0.0

            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT SUM(attendance_score) as total_score
                    FROM daily_attendance
                    WHERE student_id = ?
                """, (student_id,))

                result = cursor.fetchone()
                
                if result and result[0] is not None:
                    total_score = float(result[0])
                    if total_sessions_in_semester > 0:
                        score_out_of_10 = (total_score / total_sessions_in_semester) * 10
                        return round(score_out_of_10, 1)

                return 0.0

        except sqlite3.Error as e:
            logging.error(f"Error calculating attendance score: {e}")
            return 0.0

    def drop_all_tables(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("PRAGMA foreign_keys=OFF")
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]

                for table in tables:
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table}")
                        logging.info(f"Dropped table: {table}")
                    except sqlite3.Error as e:
                        logging.error(f"Error dropping table {table}: {e}")
                
                cursor.execute("PRAGMA foreign_keys=ON")
                
                logging.info("All tables dropped successfully")
                self._init_database()
                logging.info("Database reinitialized")

                return True

        except sqlite3.Error as e:
            logging.error(f"Error dropping tables: {e}")
            return False

    def reset_database(self):
        """Complete database reset - drops and recreates all tables"""
        try:
            logging.warning("  RESETTING DATABASE - ALL DATA WILL BE LOST!")
            return self.drop_all_tables()
        except Exception as e:
            logging.error(f"Error resetting database: {e}")
            return False

    def get_attendance_report_with_scores(self, total_sessions):
        try:
            with self.get_connection(row_factory=sqlite3.Row) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT 
                        s.name,
                        COUNT(DISTINCT da.attendance_date) as days_attended,
                        SUM(da.attendance_score) as total_score,
                        SUM(CASE WHEN da.attendance_status = 'late' THEN 1 ELSE 0 END) as late_count,
                        SUM(CASE WHEN da.attendance_status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                        SUM(da.late_minutes) as total_late_minutes
                    FROM students s
                    LEFT JOIN daily_attendance da ON s.id = da.student_id
                    GROUP BY s.id, s.name
                    ORDER BY total_score DESC, s.name
                """)

                results = [dict(row) for row in cursor.fetchall()]

                for record in results:
                    if record['total_score'] and total_sessions > 0:
                        record['score_out_of_10'] = round((float(record['total_score']) / total_sessions) * 10, 1)
                    else:
                        record['score_out_of_10'] = 0.0

                return results

        except sqlite3.Error as e:
            logging.error(f"Error getting attendance report: {e}")
            return []
