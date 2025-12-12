# Importing
import os
import sqlite3
from langchain_community.utilities import SQLDatabase

from datetime import datetime
import logging
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()


def init_sqlite_database(db_path="attendance.db", sql_path="init_sqlitedb.sql"):
    """init from init_sqlite.sql - only runs if tables don't exist"""
    try:
        import os
        import sqlite3

        print(f"\n=== init_sqlite_database() ===")
        print(f"Database: {db_path}")

        if not os.path.exists(sql_path):
            print(f"ERROR: SQL file not found: {sql_path}")
            return None

        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        existing_tables = [row[0] for row in cursor.fetchall()]

        print(f"Existing tables: {existing_tables}")

        required_tables = [
            'students',
            'attendance_sessions',
            'class_schedule',
            'semester_config',
            'student_circumstances',
            'student_daily_insights',
            'agent_analysis_log'
        ]

        missing_tables = [table for table in required_tables if table not in existing_tables]

        if not missing_tables:
            print(f"✓ All required tables exist, skipping initialization")
            conn.close()
            return SQLDatabase.from_uri(f"sqlite:///{db_path}")

        print(f"Missing tables: {missing_tables}")
        print(f"Running SQL script to create missing tables...")

        with open(sql_path, "r") as f:
            sql_script = f.read()

        cursor.executescript(sql_script)
        conn.commit()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        conn.close()
        print(f"✓ Created tables: {tables}")

        return SQLDatabase.from_uri(f"sqlite:///{db_path}")

    except Exception as e:
        print(f"Failed to init sql db: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_ai_response(ai_response, expected_values):
    """
    Parse AI response looking for lines with exactly (expected_values - 1) commas
    and exactly expected_values parts when split by commas.

    Args:
        ai_response (str): The raw AI response
        expected_values (int): Number of expected values (e.g., 3 for status,score,reason)

    Returns:
        list: Parsed values if found, None if no valid line found
    """
    try:
        expected_commas = expected_values - 1

        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Count commas in this line
            comma_count = line.count(',')

            if comma_count == expected_commas:
                parts = line.split(',')

                # Check if we have exactly the right number of parts
                if len(parts) == expected_values:
                    # All parts should have content (not empty after stripping)
                    cleaned_parts = [part.strip() for part in parts]
                    if all(cleaned_parts):
                        return cleaned_parts

        return None

    except Exception as e:
        logging.error(f"Error parsing AI response: {e}")
        return None


def get_connection(db_path="../face-reidentification/database/attendance.db", row_factory=None):
    """Connect to db"""
    conn = sqlite3.connect(db_path)
    if row_factory:
        conn.row_factory = row_factory
    return conn


def get_current_session_direct():
    """
    Get the current session, next one if it's break time
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT session_number, start_time, end_time
            FROM class_schedule
            WHERE start_time<=TIME('now','localtime') AND TIME('now','localtime') <=end_time
            LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result is None:
            query = """
                SELECT session_number, start_time, end_time
                FROM class_schedule
                WHERE TIME('now','localtime') < start_time
                ORDER BY session_number ASC
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
        if result:
            # Convert string times to time
            session_number, start_str, end_str = result
            start_time = datetime.strptime(start_str, '%H:%M:%S').time()
            end_time = datetime.strptime(end_str, '%H:%M:%S').time()

            return {
                'session_number': session_number,
                'start_time': start_time,
                'end_time': end_time
            }
        return "No active session"
    finally:
        conn.close()


def get_current_session_with_time(input_time):
    """
    Get the current session based on a specific input time
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        time_str = input_time.strftime('%H:%M:%S')

        query = """
            SELECT session_number, start_time, end_time
            FROM class_schedule
            WHERE start_time <= ? AND ? <= end_time
            LIMIT 1
        """
        cursor.execute(query, (time_str, time_str))
        result = cursor.fetchone()

        if result is None:
            query = """
                SELECT session_number, start_time, end_time
                FROM class_schedule
                WHERE ? < start_time
                ORDER BY session_number ASC
                LIMIT 1
            """
            cursor.execute(query, (time_str,))
            result = cursor.fetchone()

        if result:
            session_number, start_str, end_str = result
            start_time = datetime.strptime(start_str, '%H:%M:%S').time()
            end_time = datetime.strptime(end_str, '%H:%M:%S').time()

            return {
                'session_number': session_number,
                'start_time': start_time,
                'end_time': end_time
            }
        return "No active session"
    finally:
        conn.close()


def get_current_session_with_time(input_time):
    """
    Get the current session based on a specific input time
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        time_str = input_time.strftime('%H:%M:%S')

        query = """
            SELECT session_number, start_time, end_time
            FROM class_schedule
            WHERE start_time <= ? AND ? <= end_time
            LIMIT 1
        """
        cursor.execute(query, (time_str, time_str))
        result = cursor.fetchone()

        if result is None:
            query = """
                SELECT session_number, start_time, end_time
                FROM class_schedule
                WHERE ? < start_time
                ORDER BY session_number ASC
                LIMIT 1
            """
            cursor.execute(query, (time_str,))
            result = cursor.fetchone()

        if result:
            session_number, start_str, end_str = result
            start_time = datetime.strptime(start_str, '%H:%M:%S').time()
            end_time = datetime.strptime(end_str, '%H:%M:%S').time()

            return {
                'session_number': session_number,
                'start_time': start_time,
                'end_time': end_time
            }
        return "No active session"
    finally:
        conn.close()


def get_session_by_number(session_number: int):
    """Get the session by nunmber"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT session_number, start_time, end_time
        FROM class_schedule
        WHERE session_number = ?
        """, (session_number,))

        result = cursor.fetchone()
        if result:
            session_num, start_str, end_str = result
            start_time = datetime.strptime(start_str, '%H:%M:%S').time()
            end_time = datetime.strptime(end_str, '%H:%M:%S').time()
            return {
                'session_number': session_num,
                'start_time': start_time,
                'end_time': end_time
            }
        return None
    finally:
        conn.close()


def get_student_attendance_history(student_id):
    """Get the student history"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) as late_count,
                    SUM(CASE WHEN attendance_status = 'very_late' THEN 1 ELSE 0 END) as very_late_count,
                    AVG(late_minutes) as avg_late_minutes
                FROM attendance_sessions 
                WHERE student_id = ? 
                AND session_date >= DATE('now', '-7 days')
            """, (student_id,))
            result = cursor.fetchone()
            if result:
                total, late, very_late, avg_late = result
                # Cho cac phan tu bang None trong SQLITE
                late = late or 0
                very_late = very_late or 0
                avg_late = avg_late or 0

                return f"Last 7 days: {total} sessions, {late} late, {very_late} very late, avg{avg_late:.1f} min late"
            return "No recent history"
    except Exception as e:
        logging.error(f"Error while getting student hisotry:")
        return "History unavailable"


def active_check(student_id):
    """If the date is valid, active, if not, deactive"""
    try:

        with get_connection() as conn:
            # deactive
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, start_date, end_date
                FROM student_circumstances 
                WHERE student_id = ? AND is_active = 1
            """, (student_id,))
            results_active = cursor.fetchall()
            cursor.execute("""
                SELECT id, start_date, end_date
                FROM student_circumstances 
                WHERE student_id = ? AND is_active = 0
            """, (student_id,))
            results_deactive = cursor.fetchall()
            for result in results_active:
                cir_id, start_date, end_date = result
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                current_date = datetime.now()
                if current_date > end_date or current_date < start_date:
                    cursor.execute("""
                        UPDATE student_circumstances
                        SET is_active = 0
                        WHERE id = ?
                    """, (cir_id,))
            # active
            for result in results_deactive:
                cir_id, start_date, end_date = result
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                current_date = datetime.now()
                if current_date <= end_date and current_date >= start_date:
                    cursor.execute("""
                        UPDATE student_circumstances
                        SET is_active = 1
                        WHERE id = ?
                    """, (cir_id,))
    except Exception as e:
        print(e)


def get_student_circumstances(student_id, session_number=None):
    """Get student circumstances with session-specific excuses"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            active_check(student_id)
            if session_number:
                # Get circumstances specific to this session
                cursor.execute("""
                    SELECT circumstance_type, description, session_numbers, excuse_type
                    FROM student_circumstances 
                    WHERE student_id = ? AND is_active = 1
                    AND date('now') BETWEEN start_date AND end_date
                    AND (session_numbers = 'all' OR session_numbers LIKE ?)
                """, (student_id, f'%{session_number}%'))
            else:
                # Get all active circumstances
                cursor.execute("""
                    SELECT circumstance_type, description, session_numbers, excuse_type
                    FROM student_circumstances 
                    WHERE student_id = ? AND is_active = 1
                    AND date('now') BETWEEN start_date AND end_date
                """, (student_id,))

            results = cursor.fetchall()
            if results:
                circumstances = []
                for circ_type, description, session_nums, excuse_type in results:
                    if session_nums and excuse_type:
                        circumstances.append(f"{circ_type}({excuse_type} for sessions:{session_nums}):{description}")
                    else:
                        circumstances.append(f"{circ_type}:{description}")
                return " | ".join(circumstances)
            return "No active circumstances"
    except Exception as e:
        logging.error(f"Error getting student circumstances: {e}")
        return "Circumstances unavailable"


def get_student_name(student_id):
    """Get student name by ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
        result = cursor.fetchone()
        return result[0] if result else "Unknown"


def get_or_create_student(name):
    """Get or create student """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
        result = cursor.fetchone()

        if not result:
            cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
            student_id = cursor.lastrowid
            conn.commit()
            logging.info(f"Created new student: {name} (ID: {student_id})")
        else:
            student_id = result[0]
            logging.info(f"Found existing student: {name} (ID: {student_id})")

        conn.close()
        return student_id

    except Exception as e:
        logging.error(f"Error getting/creating student: {e}")
        return None


def calculate_late_minutes(entry_time, scheduled_start_time):
    """ calculate late minutes"""
    if isinstance(entry_time, datetime):
        entry_time = entry_time.time()
    if isinstance(scheduled_start_time, str):
        scheduled_start_time = datetime.strptime(scheduled_start_time, '%H:%M:%S').time()

    entry_datetime = datetime.combine(datetime.today(), entry_time)
    scheduled_datetime = datetime.combine(datetime.today(), scheduled_start_time)

    if entry_datetime > scheduled_datetime:
        delta = entry_datetime - scheduled_datetime
        return int(delta.total_seconds() / 60)
    return 0


def export_student_report(student_id=None, date=None, format='csv'):
    """Student attendance report"""
    if date is None:
        date = datetime.today().strftime('%Y-%m-%d')

    if format == 'csv':
        import csv

        filename = f"student_attendance_{date}.csv"

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)

            # HEADER as single row with all info
            writer.writerow(['Student ID', 'Student Name', 'Total Sessions',
                             'Attended', 'Absent', 'Late', 'Attendance %', 'Avg Score', 'Report Date'])

            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT id, name FROM students ORDER BY name")
                students = cursor.fetchall()

                for sid, name in students:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN attendance_status IN ('on_time', 'late') THEN 1 ELSE 0 END) as attended,
                            SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END) as absent,
                            SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) as late,
                            AVG(attendance_score) as avg_score
                        FROM attendance_sessions
                        WHERE student_id = ? AND session_date = ?
                    """, (sid, date))

                    result = cursor.fetchone()

                    if result and result[0] > 0:
                        total, attended, absent, late, avg_score = result
                        attendance_pct = round((attended / total) * 100, 1) if total > 0 else 0
                        writer.writerow([sid, name, total, attended, absent, late,
                                         f"{attendance_pct}%", round(avg_score or 0, 2), date])
                    else:
                        writer.writerow([sid, name, 0, 0, 0, 0, "0%", 0, date])

        return filename


def get_student_attendance_graph_data(student_id, target_date=None, days_before=30):
    """Attendance rate based on present - absent/ total"""
    if target_date is None:
        target_date = datetime.today().strftime('%Y-%m-%d')

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT date(?, ?)", (target_date, f'-{days_before} days'))
        start_date = cursor.fetchone()[0]

        cursor.execute("""
        SELECT 
            date(session_date) as day,
            -- Count by status
            COUNT(CASE WHEN attendance_status = 'absent' THEN 1 END) as absent_count,
            COUNT(CASE WHEN attendance_status != 'absent' THEN 1 END) as present_count,
            COUNT(*) as total_sessions
        FROM attendance_sessions 
        WHERE student_id = ? 
          AND session_date >= ? 
          AND session_date <= ?
        GROUP BY date(session_date)
        ORDER BY day
        """, (student_id, start_date, target_date))

        # Calculate present rate
        results = []
        for day, absent, present, total in cursor.fetchall():
            if total > 0:
                present_rate = round((present / total) * 100, 1)
            else:
                present_rate = 0

            results.append((day, absent, present, total, present_rate))

        return results


def get_teacher_dashboard(self, date=None):
    """Combine everything already have into one view"""
    if date is None:
        date = datetime.today().strftime('%Y-%m-%d')

    return {
        'date': date,
        'today_summary': self.get_session_attendance(date),
        'weekly_trends': self.get_weekly_attendance_stats(date),
        'high_priority': self.get_high_priority_students(),
    }
