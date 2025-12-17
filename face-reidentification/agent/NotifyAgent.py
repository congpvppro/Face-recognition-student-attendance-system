from Utility import get_connection
from datetime import datetime
from sqlite3 import Error

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from sqlite3 import Error


class NotifyAgent:
    def __init__(self):
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()

    @staticmethod
    def get_expected_students():
        """
        Get the complete list of all enrolled students with their IDs and names. 
        Returns a list of tuples like [(1, "John Smith"), (2, "Jane Doe"), ...]
        """
        try:
            with get_connection() as conn:
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
    def get_present_students():
        """
        Get only the student IDs of students who are marked present today. 
        Returns a list of student IDs like [1, 2, 3] or "No present students".
        """
        try:
            with get_connection() as conn:
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
    def get_missing_students():
        """
        Get the list of students who are missing today.
        Returns a list of tuples with (id, name) for missing students.
        """
        students = NotifyAgent.get_expected_students()
        presented = NotifyAgent.get_present_students()

        if presented == "No present students":
            return [student[0] for student in students]  # All students are missing

        present_ids = set(presented)

        return [student[0] for student in students if student[0] not in present_ids]

    def notify_missing_students(self):
        """
        Send email notifications to parents of missing students using SendGrid.
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("PRAGMA table_info(students)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]


                cursor.execute("PRAGMA table_info(students);")
                for col in cursor.fetchall():
                    print(col)

                if 'parent_email' not in column_names:
                    print("ERROR: 'parent_email' column missing! Add it with:")
                    print("ALTER TABLE students ADD COLUMN parent_email TEXT;")
                    print("UPDATE students SET parent_email = 'ducduy1982005@gmail.com';")
                    return

                print(f"Database columns: {column_names}")

                today = datetime.now().strftime('%Y-%m-%d')
                print(f"Checking attendance for: {today}")

                missing_ids = self.get_missing_students()[:1]

                if not missing_ids:
                    print("No missing students today")
                    return

                print(f"Found {len(missing_ids)} missing student(s)")

                placeholders = ','.join(['?'] * len(missing_ids))
                cursor.execute(f"""
                    SELECT name, parent_email 
                    FROM students 
                    WHERE id IN ({placeholders})
                """, missing_ids)

                students_data = cursor.fetchall()

                if not students_data:
                    print("No parent emails found")
                    return

            # 5. Send emails
            sendgrid_key = os.getenv("SENDGRID_API_KEY")
            if not sendgrid_key:
                print("No SendGrid API key")
                return

            sg = SendGridAPIClient(sendgrid_key)
            successful = 0

            for student_name, parent_email in students_data:
                print(f"Sending to {student_name}'s parent: {parent_email}")

                message = Mail(
                    from_email="schoolworkjdoe@gmail.com",
                    to_emails=parent_email,
                    subject=f"{student_name} Absent Today",
                    html_content=f"<p>Your child {student_name} was absent today ({today}).</p>"
                )
                message.reply_to = "schoolworkjdoe@gmail.com"

                try:
                    response = sg.send(message)
                    print(f"  Sent. Status: {response.status_code}")
                    successful += 1
                except Exception as e:
                    print(f"  Failed: {e}")

            print(f"Done. Sent {successful}/{len(students_data)} emails")

        except Exception as e:
            print(f"Error: {e}")