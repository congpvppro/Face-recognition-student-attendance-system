import sqlite3
from datetime import datetime
import datetime as dt
from contextlib import contextmanager
import logging
import os
from agent.Utility import get_or_create_student
from agent.RecordAgent import RecordAgent
from agent.Utility import get_connection
from sqlite3 import Error
from agent.Utility import init_sqlite_database
from agent.Utility import get_current_session_direct, calculate_late_minutes, get_or_create_student
from agent.NotifyAgent import NotifyAgent

class AttendanceDatabase:

    def __init__(self, db_path='attendance.db', sql_path = "init_sqlitedb.sql"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.connection = get_connection()
        init_sqlite_database(db_path, sql_path)
        self.record_agent = RecordAgent()

    def get_connection(self):
        return get_connection(self.db_path)
    def _str_to_time(self, time_str):
        if isinstance(time_str, str):
            return datetime.strptime(time_str, '%H:%M:%S').time()
        return time_str

    def get_current_session_time(self):
        return get_current_session_direct()

    def calculate_late_minutes(self, entry_time, scheduled_start_time):
        calculate_late_minutes(entry_time, scheduled_start_time)

    def record_entry(self, name):
        self.record_agent.record_entry(name)

    def record_exit(self, name):
        self.record_agent.record_exit(name)

        # def get_current_status(self, name):
        #     try:
        #         with self.connection as conn:
        #             cursor = conn.cursor()
        #             current_date = datetime.now().strftime('%Y-%m-%d')
        #
        #             cursor.execute("""
        #                         SELECT da.current_status
        #                         FROM daily_attendance da
        #                         JOIN students s ON da.student_id = s.id
        #                         WHERE s.name = ? AND da.attendance_date = ?
        #                     """, (name, current_date))
        #
        #             result = cursor.fetchone()
        #             return result[0] if result else 'absent'
        #
        #     except sqlite3.Error as e:
        #         logging.error(f"Error getting status: {e}")
        #         return 'absent'

    # def get_daily_report(self, date=None):
    #     try:
    #         with self.connection as conn:
    #             cursor = conn.cursor()
    #             target_date = date or datetime.now().strftime('%Y-%m-%d')
    #
    #             cursor.execute("""
    #                         SELECT
    #                             s.name,
    #                             da.total_sessions,
    #                             da.total_minutes,
    #                             da.first_entry,
    #                             da.last_exit,
    #                             da.current_status
    #                         FROM daily_attendance da
    #                         JOIN students s ON da.student_id = s.id
    #                         WHERE da.attendance_date = ?
    #                         ORDER BY s.name
    #                     """, (target_date,))
    #
    #             return [dict(row) for row in cursor.fetchall()]
    #
    #     except sqlite3.Error as e:
    #         logging.error(f"Error getting daily report: {e}")
    #         return []

    def get_current_students(self):
        return NotifyAgent.get_present_students()

    def get_absent_students(self, registered_students):
        return NotifyAgent.get_missing_students()

    def mark_absent(self, name):
        try:
            student_id = get_or_create_student(name)
            if student_id is None:
                return False

            with get_connection(self.db_path) as conn:
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

            with get_connection(self.db_path) as conn:
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
            with get_connection(self.db_path) as conn:
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
            with self.connection as conn:
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
