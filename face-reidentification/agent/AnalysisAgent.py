from datetime import datetime, date
from Utility import get_connection
import logging
from Utility import get_student_name, active_check, get_student_circumstances
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

class AnalysisAgent:

    def __init__(self):
        self.connection = get_connection()
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        load_dotenv()
        self.llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"),
                            model_name="llama-3.3-70b-versatile",
                            temperature=0)

    @staticmethod
    def generate_daily_insights():
        """
        Scheduled to generated daily insights
        used for recommendation, prioritizing students, etc.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            today = date.today().isoformat()
            # Check all the active circumstances first!
            result = cursor.execute("""
                                    SELECT student_id
                                    FROM student_circumstances
                                    """).fetchall()
            for student_id in result:
                active_check(student_id[0])

            cursor.execute("DELETE FROM student_daily_insights WHERE date = ?", (today,))

            cursor.execute("""
                INSERT INTO student_daily_insights 
                (date, student_id, student_name, sessions_attended, sessions_late, full_day_absent, has_circumstances,
                 priority_score)
                SELECT 
                    ? as date,
                    s.id as student_id, 
                    s.name as student_name,
                    COUNT(CASE WHEN a.attendance_status IN ('on_time', 'late') THEN 1 END) as sessions_attended,
                    COUNT(CASE WHEN a.attendance_status = 'late' THEN 1 END) as sessions_late,
                    CASE WHEN COUNT(a.id) = 0 THEN 1 ELSE 0 END as full_day_absent,
                    CASE WHEN sc.id IS NOT NULL THEN 1 ELSE 0 END as has_circumstances,
                    CASE 
                        WHEN COUNT(a.id) = 0 THEN 10
                        WHEN COUNT(CASE WHEN a.attendance_status = 'late' THEN 1 END) > 2 THEN 8
                        WHEN COUNT(CASE WHEN a.attendance_status = 'late' THEN 1 END) > 0 THEN 5
                        ELSE 1
                    END as priority_score
                FROM students s
                LEFT JOIN attendance_sessions a ON s.id = a.student_id AND a.session_date = ?
                LEFT JOIN student_circumstances sc ON s.id = sc.student_id AND sc.is_active = 1
                GROUP BY s.id, s.name
            """, (today, today))

            conn.commit()
            conn.close()
            return f"Insights generated for {today}"
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def get_weekly_attendance_stats(end_date=None, days_back=7):
        """Get stats for any period"""
        if end_date is None:
            end_date = datetime.today().strftime('%Y-%m-%d')

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT date(?, ?)", (end_date, f'-{days_back} days'))
            start_date = cursor.fetchone()[0]

            cursor.execute("""
                SELECT 
                    date(session_date) as day,
                    ROUND(COUNT(CASE WHEN attendance_status = 'on_time' OR 'excused' THEN 1 END) * 100.0 / COUNT(*), 1) 
                    as on_time_pct,
                    ROUND(COUNT(CASE WHEN attendance_status = 'late' THEN 1 END) * 100.0 / COUNT(*), 1) as late_pct,
                    ROUND(COUNT(CASE WHEN attendance_status = 'absent' THEN 1 END) * 100.0 / COUNT(*), 1) as absent_pct
                FROM attendance_sessions 
                WHERE session_date >= ? AND session_date <= ?
                GROUP BY date(session_date)
                ORDER BY day
            """, (start_date, end_date))
            return cursor.fetchall()

    @staticmethod
    def get_high_priority_students():
        """
        Get students with average priority > 5 in last 7 days
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            SELECT 
                student_id,
                student_name,
                ROUND(AVG(priority_score), 2) as avg_priority,
                COUNT(*) as days_with_issues
            FROM student_daily_insights 
            WHERE date >= date('now', '-7 days') AND priority_score > 1
            GROUP BY student_id, student_name
            HAVING AVG(priority_score) >=5
            ORDER BY avg_priority DESC;
            """)
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def get_intervention_history(student_id):
        """Get recent intervention history for a student"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT reason,recommendation, intervention_effective, analysis_date
                FROM agent_analysis_log 
                WHERE student_id = ? 
                AND intervention_effective IS NOT NULL
                ORDER BY analysis_date DESC 
                LIMIT 3  -- Get last 3 interventions for pattern recognition
            """, (student_id,))
            results = cursor.fetchall()
            return results if results else None

    def analysis_student_problems(self):
        """
        Analysis student problems in batches of 6 with intervention history consideration
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                high_priority_students = self.get_high_priority_students()

                high_priority_students = [
                    [student_id, a, b, c, get_student_circumstances(student_id),
                     self.get_intervention_history(student_id)]
                    for student_id, a, b, c in high_priority_students]

                analysis_list = []
                for i in range(0, min(6, len(high_priority_students)), 3):
                    batch_students = high_priority_students[i:i + 3]

                    prompt = f"""
                    Analyze these {len(batch_students)} students with circumstances AND past intervention history:
                    {batch_students}

                    Output ONLY lines in format:
                    student_id|alert_level|reason|recommendation

                    **STRICT RULES - NO HALLUCINATION:**
                    - Check if circumstances list is EMPTY [] or None → NO valid circumstances
                    - Check if circumstances match the attendance issue type
                    - CONSIDER PAST INTERVENTION EFFECTIVENESS when making recommendations

                    **Decision Rules:**
                    - HIGH: 3+ absences AND no valid circumstances
                    - MEDIUM: 1-2 absences AND no valid circumstances  
                    - LOW: ONLY if circumstances list is NOT empty AND circumstances are active AND cover today

                    **INTERVENTION HISTORY CONSIDERATION:**
                    - intervention_effective = 1: Previous intervention WORKED
                    - intervention_effective = 0: Previous intervention FAILED  
                    - intervention_effective = NULL: Intervention not yet evaluated (too recent)
                    - No records: First time intervention

                    **SPECIFIC RECOMMENDATION STRATEGIES - BE SPECIFIC:**
                    - WORKED (1): "Continue [specific successful approach]"
                    - FAILED (0): CHOOSE ONE OR SUGGESTS ONE: "Escalate to counselor", "Schedule in-person meeting", "Home visit", 
                    "Academic support referral", "Behavioral intervention"
                    - NULL (recent): "Follow up on [recent intervention]" 
                    - NO HISTORY: "Contact parents", "Schedule meeting", "Monitor attendance"

                    **ESCALATION PATH FOR FAILED INTERVENTIONS:**
                    - 1st failure: Try different contact method (phone → in-person)
                    - 2nd failure: Escalate to school counselor
                    - 3rd+ failure: Involve administration/principal

                    **VALID CIRCUMSTANCES REQUIRE:**
                    - is_active=1
                    - Current date between start_date and end_date  
                    - excuse_type matches the issue (late_arrival for lateness, etc.)

                    **Examples - BE SPECIFIC:**
                    49|medium|1 absence, previous parent contact failed|Escalate to school counselor
                    59|medium|2 absences, previous meeting ineffective|Schedule in-person parent conference
                    1|low|Valid circumstances, bus monitoring worked|Continue bus schedule coordination

                    Start with student_id. No extra text.
                    """

                    response = self.llm.invoke(prompt)
                    analysis_text = response.content

                    # Parsing the response
                    for line in analysis_text.strip().split('\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 4:
                                clean_id = parts[0].replace('.', '').strip()
                                analysis_list.append({
                                    'student_id': int(clean_id),
                                    'student_name': get_student_name(clean_id),
                                    'alert_level': parts[1].strip(),
                                    'reason': parts[2].strip(),
                                    'recommendation': parts[3].strip()
                                })

                    # INSERT into database
                    for student in analysis_list:
                        try:
                            cursor.execute("""INSERT INTO agent_analysis_log 
                                    (student_id, student_name, alert_level, reason, recommendation,
                                     created_at, analysis_date)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                           (student['student_id'], student['student_name'],
                                            student['alert_level'], student['reason'],
                                            student['recommendation'], date.today().isoformat(),
                                            date.today().isoformat()))
                        except Exception as e:
                            print(f" Failed to insert {student['student_id']}: {e}")
                            continue

                    conn.commit()
                return analysis_list
        except Exception as e:
            logging.warning(f"Error in analysis_student_problems: {e}")
            return None

    @staticmethod
    def evaluate_past_interventions():
        """
        Mark previous interventions as worked or not based on attendance rate comparison
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Get unevaluated interventions from 3-10 days ago
                cursor.execute("""
                    SELECT 
                        a.id as log_id,
                        a.student_id,
                        a.analysis_date
                    FROM agent_analysis_log a
                    WHERE a.analysis_date BETWEEN date('now', '-10 days') AND date('now', '-3 days')
                    AND a.intervention_effective IS NULL
                """)

                interventions = cursor.fetchall()

                for log_id, student_id, analysis_date in interventions:
                    # Get attendance rate before intervention (3 days before)
                    cursor.execute("""
                        SELECT COUNT(*) FROM attendance_sessions 
                        WHERE student_id = ? 
                        AND session_date BETWEEN date(?, '-3 days') AND ?
                        AND attendance_status IN ('on_time', 'late')
                    """, (student_id, analysis_date, analysis_date))
                    before_count = cursor.fetchone()[0]

                    # Get attendance rate after intervention (3 days after)
                    cursor.execute("""
                        SELECT COUNT(*) FROM attendance_sessions 
                        WHERE student_id = ? 
                        AND session_date BETWEEN date(?, '+1 day') AND date(?, '+4 days')
                        AND attendance_status IN ('on_time', 'late')
                    """, (student_id, analysis_date, analysis_date))
                    after_count = cursor.fetchone()[0]

                    # Mark as effective if improvement
                    effective = 1 if after_count > before_count else 0

                    cursor.execute("""
                        UPDATE agent_analysis_log 
                        SET intervention_effective = ?
                        WHERE id = ?
                    """, (effective, log_id))

                conn.commit()
                print(f"Evaluated {len(interventions)} interventions")
                return len(interventions)

        except Exception as e:
            print(f"Error: {e}")
            return 0

    @staticmethod
    def get_student_analysis(student_id):
        """Get recent analysis results"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                student_name, 
                alert_level, 
                reason, 
                recommendation,
                analysis_date,
                intervention_effective
            FROM agent_analysis_log 
            WHERE student_id = ?
            ORDER BY created_at DESC 
            """, (student_id,))
            return cursor.fetchall()

    @staticmethod
    # used to show on the graph the reason for student score on that day
    def get_session_attendance(date=None):
        """Show attendance per class period """
        if date is None:
            date = datetime.today().strftime('%Y-%m-%d')

        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
            SELECT 
                cs.session_number,
                cs.start_time,
                cs.end_time,
                COUNT(DISTINCT a.student_id) as students_present,
                SUM(CASE WHEN a.attendance_status = 'late' THEN 1 ELSE 0 END) as late_count,
                SUM(CASE WHEN a.attendance_status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                a.attendance_score
            FROM class_schedule cs
            LEFT JOIN attendance_sessions a ON cs.session_number = a.session_number 
                AND a.session_date = ?
            GROUP BY cs.session_number
            ORDER BY cs.session_number
            """, (date,))

            return cursor.fetchall()

    @staticmethod
    def export_student_report(student_id=None, date=None, format='both'):
        """export student report - generates both CSV and Excel files"""
        try:
            from openpyxl import Workbook
            import csv

            if date is None:
                base_filename = "student_attendance_TOTAL_SUMMARY"
            else:
                base_filename = f"student_attendance_{date}"

            excel_filename = f"{base_filename}.xlsx"
            csv_filename = f"{base_filename}.csv"

            data = []
            headers = ['Student ID', 'Student Name', 'Total Sessions',
                       'Attended', 'Absent', 'Late', 'Attendance %', 'Avg Score']

            if date is not None:
                headers.append('Report Date')

            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT id, name FROM students ORDER BY name")
                students = cursor.fetchall()

                for sid, name in students:
                    if date is None:
                        cursor.execute("""
                            SELECT 
                                COUNT(*) as total,
                                SUM(CASE WHEN attendance_status IN ('on_time', 'late') THEN 1 ELSE 0 END) as attended,
                                SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END) as absent,
                                SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) as late,
                                AVG(attendance_score) as avg_score
                            FROM attendance_sessions
                            WHERE student_id = ?
                        """, (sid,))
                    else:
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

                        if date is None:
                            row = [sid, name, total, attended, absent, late,
                                   f"{attendance_pct}%", round(avg_score or 0, 2)]
                        else:
                            row = [sid, name, total, attended, absent, late,
                                   f"{attendance_pct}%", round(avg_score or 0, 2), date]
                    else:
                        if date is None:
                            row = [sid, name, 0, 0, 0, 0, "0%", 0]
                        else:
                            row = [sid, name, 0, 0, 0, 0, "0%", 0, date]

                    data.append(row)

            if format in ['excel', 'both']:
                wb = Workbook()
                ws = wb.active

                if date is None:
                    ws.title = "Total Summary Report"
                else:
                    ws.title = f"Attendance Report {date}"

                ws.append(headers)
                for row in data:
                    ws.append(row)

                wb.save(excel_filename)

            if format in ['csv', 'both']:
                with open(csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                    writer.writerows(data)

            if format == 'excel':
                return excel_filename
            elif format == 'csv':
                return csv_filename
            else:  # 'both'
                return {'excel': excel_filename, 'csv': csv_filename}

        except ImportError:
            return None
