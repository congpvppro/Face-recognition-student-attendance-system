import mysql.connector
from datetime import datetime
import datetime as dt
from contextlib import contextmanager
import logging

class AttendanceDatabase:

    def __init__(self, host='localhost', port=3306, user='root', password='07112005', database='attendance_db'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self._init_database()

    def _init_database(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()

            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.execute(f"USE {self.database}")

            # Create students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    session_date DATE NOT NULL,
                    entry_time DATETIME NOT NULL,
                    exit_time DATETIME,
                    duration_minutes INT,
                    status ENUM('present', 'left') DEFAULT 'present',
                    attendance_status ENUM('on_time', 'late', 'absent') DEFAULT 'on_time',
                    late_minutes INT DEFAULT 0,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    INDEX idx_date_status (session_date, status)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    attendance_date DATE NOT NULL,
                    total_sessions INT DEFAULT 0,
                    total_minutes INT DEFAULT 0,
                    first_entry DATETIME,
                    last_exit DATETIME,
                    current_status ENUM('present', 'absent') DEFAULT 'absent',
                    attendance_status ENUM('on_time', 'late', 'absent') DEFAULT 'absent',
                    late_minutes INT DEFAULT 0,
                    attendance_score DECIMAL(3,1) DEFAULT 0,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    UNIQUE KEY unique_daily_attendance (student_id, attendance_date)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS class_schedule (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_number INT NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    UNIQUE KEY unique_session (session_number)
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
                    VALUES (%s, %s, %s)
                """, schedule_data)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semester_config (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    semester_name VARCHAR(100) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    total_sessions INT DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()
            logging.info("Database initialized successfully")

        except mysql.connector.Error as e:
            logging.error(f"Error initializing database: {e}")
            raise

    def _timedelta_to_time(self, td):
        """Convert timedelta to time object"""
        if isinstance(td, dt.timedelta):  # CHANGE: Use dt.timedelta
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return dt.time(hour=hours, minute=minutes, second=seconds)  # CHANGE: Use dt.time
        elif isinstance(td, dt.time):  # CHANGE: Use dt.time
            return td
        else:
            return td
    def get_current_session_time(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now().time()

                cursor.execute("""
                    SELECT session_number, start_time, end_time 
                    FROM class_schedule
                    WHERE start_time <= %s AND end_time >= %s
                    ORDER BY start_time DESC
                    LIMIT 1
                """, (current_time, current_time))

                result = cursor.fetchone()

                if result:
                    cursor.close()
                    return {
                        'session_number': result[0],
                        'start_time': self._timedelta_to_time(result[1]),
                        'end_time': self._timedelta_to_time(result[2])
                    }

                cursor.execute("""
                    SELECT session_number, start_time, end_time 
                    FROM class_schedule
                    WHERE start_time > %s
                    ORDER BY start_time ASC
                    LIMIT 1
                """, (current_time,))

                result = cursor.fetchone()
                cursor.close()

                if result:
                    return {
                        'session_number': result[0],
                        'start_time': self._timedelta_to_time(result[1]),
                        'end_time': self._timedelta_to_time(result[2])
                    }

                return None

        except mysql.connector.Error as e:
            logging.error(f"Error getting current session: {e}")
            return None
    def calculate_late_minutes(self, entry_time, scheduled_start_time):

        scheduled_time = self._timedelta_to_time(scheduled_start_time)

        if isinstance(entry_time, dt.datetime):
            entry_time = entry_time.time()

        entry_datetime = datetime.combine(datetime.today(), entry_time)
        scheduled_datetime = datetime.combine(datetime.today(), scheduled_time)

        if entry_datetime > scheduled_datetime:
            delta = entry_datetime - scheduled_datetime
            return int(delta.total_seconds() / 60)
        return 0
    @contextmanager
    def get_connection(self):
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
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
                cursor.execute("SELECT id FROM students WHERE name = %s", (name,))
                result = cursor.fetchone()

                if not result:
                    cursor.execute("INSERT INTO students (name) VALUES (%s)", (name,))
                    student_id = cursor.lastrowid
                else:
                    student_id = result[0]

                cursor.close()
                return student_id
        except mysql.connector.Error as e:
            logging.error(f"Error getting/creating student: {e}")
            return None

    def record_entry(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                student_id = self.get_or_create_student(name)

                current_datetime = datetime.now()
                current_date = current_datetime.date()
                current_time = current_datetime.time()

                # Get current session info
                session_info = self.get_current_session_time()

                if not session_info:
                    logging.warning("No active session found")
                    cursor.close()
                    return None

                # Calculate if late
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

                # Create new session
                cursor.execute("""
                    INSERT INTO attendance_sessions 
                    (student_id, session_date, entry_time, status, attendance_status, late_minutes)
                    VALUES (%s, %s, %s, 'present', %s, %s)
                """, (student_id, current_date, current_datetime, attendance_status, late_minutes))

                session_id = cursor.lastrowid

                # Update daily summary
                cursor.execute("""
                    INSERT INTO daily_attendance 
                    (student_id, attendance_date, total_sessions, first_entry, current_status, 
                     attendance_status, late_minutes, attendance_score)
                    VALUES (%s, %s, 1, %s, 'present', %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        total_sessions = total_sessions + 1,
                        current_status = 'present',
                        first_entry = LEAST(first_entry, %s),
                        attendance_status = IF(attendance_status = 'on_time', attendance_status, %s),
                        late_minutes = late_minutes + %s,
                        attendance_score = attendance_score + %s
                """, (student_id, current_date, current_datetime, attendance_status, late_minutes,
                      attendance_score, current_datetime, attendance_status, late_minutes, attendance_score))

                cursor.close()
                logging.info(f"Entry recorded for {name} at {current_datetime.strftime('%H:%M:%S')}")
                return session_id

        except mysql.connector.Error as e:
            logging.error(f"Error recording entry: {e}")
            return None

    def record_exit(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                student_id = self.get_or_create_student(name)

                current_datetime = datetime.now()
                current_date = current_datetime.date()

                # Find the most recent open session
                cursor.execute("""
                    SELECT id, entry_time FROM attendance_sessions
                    WHERE student_id = %s 
                    AND session_date = %s 
                    AND status = 'present'
                    ORDER BY entry_time DESC
                    LIMIT 1
                """, (student_id, current_date))

                result = cursor.fetchone()

                if result:
                    session_id, entry_time = result
                    duration = int((current_datetime - entry_time).total_seconds() / 60)

                    # Update session
                    cursor.execute("""
                        UPDATE attendance_sessions
                        SET exit_time = %s, duration_minutes = %s, status = 'left'
                        WHERE id = %s
                    """, (current_datetime, duration, session_id))

                    # Update daily summary
                    cursor.execute("""
                        UPDATE daily_attendance
                        SET total_minutes = total_minutes + %s,
                            last_exit = %s,
                            current_status = 'absent'
                        WHERE student_id = %s AND attendance_date = %s
                    """, (duration, current_datetime, student_id, current_date))

                    cursor.close()
                    logging.info(
                        f" Exit recorded for {name} at {current_datetime.strftime('%H:%M:%S')} (Duration: {duration} min)")
                    return True
                else:
                    logging.warning(f"No open session found for {name}")
                    cursor.close()
                    return False

        except mysql.connector.Error as e:
            logging.error(f"Error recording exit: {e}")
            return False

    def get_current_status(self, name):
        """Check if student is currently in class"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().date()

                cursor.execute("""
                    SELECT da.current_status
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE s.name = %s AND da.attendance_date = %s
                """, (name, current_date))

                result = cursor.fetchone()
                cursor.close()

                return result[0] if result else 'absent'

        except mysql.connector.Error as e:
            logging.error(f"Error getting status: {e}")
            return 'absent'

    def get_daily_report(self, date=None):
        """Get daily attendance report"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                target_date = date or datetime.now().date()

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
                    WHERE da.attendance_date = %s
                    ORDER BY s.name
                """, (target_date,))

                results = cursor.fetchall()
                cursor.close()
                return results

        except mysql.connector.Error as e:
            logging.error(f"Error getting daily report: {e}")
            return []

    def get_current_students(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().date()

                cursor.execute("""
                    SELECT s.name
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE da.attendance_date = %s AND da.current_status = 'present'
                    ORDER BY s.name
                """, (current_date,))

                results = cursor.fetchall()
                cursor.close()

                return [row[0] for row in results]

        except mysql.connector.Error as e:
            logging.error(f"Error getting current students: {e}")
            return []

    def get_today_attendance(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().date()

                cursor.execute("""
                    SELECT COUNT(*) FROM attendance
                    WHERE attendance_date = %s
                """, current_date)

                result = cursor.fetchone()
                cursor.close()

                return result[0] if result else 0

        except mysql.connector.Error as e:
            logging.error(f"Error getting attendance: {e}")
            return 0

    def get_absent_students(self, registered_students):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().date()

                # Get students who are present today
                cursor.execute("""
                    SELECT s.name
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE da.attendance_date = %s
                """, (current_date,))

                present_students = set([row[0] for row in cursor.fetchall()])
                cursor.close()

                # Find absent students
                absent_students = set(registered_students) - present_students
                return list(absent_students)

        except mysql.connector.Error as e:
            logging.error(f"Error getting absent students: {e}")
            return []

    def mark_absent(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                student_id = self.get_or_create_student(name)
                current_date = datetime.now().date()

                cursor.execute("""
                    INSERT INTO daily_attendance 
                    (student_id, attendance_date, attendance_status, attendance_score, current_status)
                    VALUES (%s, %s, 'absent', 0, 'absent')
                    ON DUPLICATE KEY UPDATE
                        attendance_status = 'absent',
                        current_status = 'absent'
                """, (student_id, current_date))

                cursor.close()
                logging.info(f"Marked {name} as absent")
                return True

        except mysql.connector.Error as e:
            logging.error(f"Error marking absent: {e}")
            return False

    def calculate_attendance_score(self, name, total_sessions_in_semester):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                student_id = self.get_or_create_student(name)

                # Get total attendance score for the semester
                cursor.execute("""
                    SELECT SUM(attendance_score) as total_score, COUNT(*) as days_recorded
                    FROM daily_attendance
                    WHERE student_id = %s
                """, (student_id,))

                result = cursor.fetchone()
                cursor.close()

                if result and result[0] is not None:
                    total_score = float(result[0])
                    days_recorded = result[1]

                    # Calculate score out of 10
                    if total_sessions_in_semester > 0:
                        score_out_of_10 = (total_score / total_sessions_in_semester) * 10
                        return round(score_out_of_10, 1)

                return 0.0

        except mysql.connector.Error as e:
            logging.error(f"Error calculating attendance score: {e}")
            return 0.0

    def drop_all_tables(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Disable foreign key checks temporarily
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

                # Drop tables in reverse order of dependencies
                tables_to_drop = [
                    'daily_attendance',
                    'attendance_sessions',
                    'semester_config',
                    'class_schedule',
                    'students'
                ]

                for table in tables_to_drop:
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table}")
                        logging.info(f"Dropped table: {table}")
                    except mysql.connector.Error as e:
                        logging.error(f"Error dropping table {table}: {e}")

                # Re-enable foreign key checks
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

                cursor.close()
                logging.info("All tables dropped successfully")

                # Reinitialize the database
                self._init_database()
                logging.info("Database reinitialized")

                return True

        except mysql.connector.Error as e:
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
        """Get detailed attendance report with scores"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

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

                results = cursor.fetchall()
                cursor.close()

                # Calculate score out of 10 for each student
                for record in results:
                    if record['total_score'] and total_sessions > 0:
                        record['score_out_of_10'] = round((float(record['total_score']) / total_sessions) * 10, 1)
                    else:
                        record['score_out_of_10'] = 0.0

                return results

        except mysql.connector.Error as e:
            logging.error(f"Error getting attendance report: {e}")
            return []
