from Utility import get_connection
from datetime import datetime
from sqlite3 import Error


class NotifyAgent:
    def __init__(self):
        self.connection = get_connection()

    def get_expected_students(self):
        """
        Get the complete list of all enrolled students with their IDs and names. 
        Returns a list of tuples like [(1, "John Smith"), (2, "Jane Doe"), ...]
        """
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT id, name
                FROM students
                """)
                return cursor.fetchall()
        except Error as e:
            print(e)
            return None
    @staticmethod
    def get_present_students(self):
        """
        Get only the student IDs of students who are marked present today. 
        Returns a list of student IDs like [1, 2, 3] or "No present students".
        """
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                current_date = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                SELECT DISTINCT student_id
                FROM attendance_sessions
                WHERE session_date = ?
                """, (current_date,))
                result = cursor.fetchall()
                # Extract just the IDs from tuples
                return [row[0] for row in result] if result else "No present students"
        except Error as e:
            print(e)
            return None
    @staticmethod
    def get_missing_students(self):
        """
        Get the list of students who are missing today.
        Returns a list of tuples with (id, name) for missing students.
        """
        students = self.get_expected_students()
        presented = self.get_present_students()

        if presented == "No present students":
            return [student[0] for student in students]  # All students are missing

        present_ids = set(presented)

        return [student[0] for student in students if student[0] not in present_ids]

    def notify_missing_students(self, missing_students):
        """
        Send notifications to missing students. 
        Input should be a list of student IDs that are absent today.
        Call this after identifying which students are missing by comparing 
        expected students with present students.
        Example: [1, 5, 7, 9] or [1, 3, 8, 12]
        """
        print(f"Notifying missing students: {missing_students}")
