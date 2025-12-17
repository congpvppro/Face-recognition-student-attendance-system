import os
from Utility import init_sqlite_database, get_connection, get_student_circumstances
from Utility import get_student_attendance_history, parse_ai_response, calculate_late_minutes
from Utility import (get_or_create_student, get_session_by_number, get_current_session_direct,
                     get_current_session_with_time)
from langchain_groq import ChatGroq
import logging
from datetime import datetime
from dotenv import load_dotenv




class RecordAgent:

    def __init__(self, db_path="../database/attendance.db", sql_path = "../database/init_sqlitedb.sql"):
        load_dotenv()
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.connection = get_connection(self.db_path)
        # init_sqlite_database(db_path, sql_path)
        self.llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"),
                            model_name="llama-3.3-70b-versatile",
                            temperature=0)

    def calculate_auto_fill_score(self, student_id, session_num, student_name, is_entry):
        """Determining the score based on circumstances and stuff"""

        student_circumstances = get_student_circumstances(student_id, session_num)
        if is_entry:
            # Check circumstances for sessions BEFORE current
            ai_prompt = f"""
              AUTO-FILL SCORING FOR ENTRY:

              STUDENT: {student_name}
              SESSION: {session_num} (session being auto-filled)
              FIRST ENTRY: TRUE
              CIRCUMSTANCES: {student_circumstances}

              SCORING RULES FOR SESSIONS BEFORE ENTRY (STRICT - FOLLOW EXACTLY):
              - 'excused' (score: 1.0): Student has 'full' excuse for this specific session
              - 'excused' (score: 0.5): Student has 'partial' or 'late_arrival' excuse for this session  
              - 'absent' (score: 0.0): No valid documented excuse for this session

              STATUS RULES FOR FIRST ENTRY:
              • Use 'excused' ONLY if circumstances specifically mention this session number
              • Use 'absent' if no valid excuse exists
              • DO NOT use 'on_time' or 'late' for auto-filled first entry sessions

              Return ONLY: status,score,reason
              Valid Examples:
              excused,1.0,has_medical_excuse_for_session_{session_num}
              excused,0.5,has_transportation_issues_documented
              absent,0.0,no_documented_excuse_for_this_session

              Your decision (ONLY use 'excused' or 'absent'):
              """
        else:
            # Between last entry and current exit
            ai_prompt = f"""
              AUTO-FILL SCORING FOR MISSED SESSION:

              STUDENT: {student_name}
              SESSION: {session_num} (session being auto-filled)
              CIRCUMSTANCES: {student_circumstances}

              SCORING RULES FOR MISSED SESSIONS BETWEEN RECORDED ENTRIES (STRICT - FOLLOW EXACTLY):
              - 'on_time' (score: 1.0): Assume student was present but forgot to record entry (default)
              - 'absent' (score: 0.0): Only if clear evidence of absence from circumstances

              STATUS RULES FOR MISSED SESSIONS:
              • Use 'on_time' as default assumption (student was present between scans)
              • Use 'absent' ONLY if clear evidence they were missing
              • DO NOT use 'late' or 'excused' for auto-filled between sessions

              Return ONLY: status,score,reason
              Valid Examples:
              on_time,1.0,assumed_present_between_recorded_sessions
              on_time,1.0,student_likely_present_based_on_movement_pattern
              absent,0.0,clear_evidence_of_absence_from_circumstances

              Your decision (ONLY use 'on_time' or 'absent'):
              """

        ai_response = self.llm.invoke(ai_prompt).content.strip()
        print(f"AI Response: {ai_response}")

        parsed_values = parse_ai_response(ai_response, 3)

        if parsed_values and len(parsed_values) == 3:
            status, score_str, reason = parsed_values
            try:
                score = float(score_str)

                if is_entry:
                    allowed_statuses = ['excused', 'absent']
                else:
                    allowed_statuses = ['on_time', 'absent']

                if status not in allowed_statuses:
                    logging.warning(f"Invalid status '{status}' for context, using fallback")
                    status = 'absent' if is_entry else 'on_time'
                    score = 0.0 if is_entry else 1.0
                    reason = f'fallback_invalid_status_{reason}'

                # Validate score range
                if score < 0 or score > 1:
                    score = max(0.0, min(1.0, score))

                return {
                    'status': status,
                    'score': score,
                    'reason': reason
                }

            except ValueError:
                logging.warning(f"Invalid score format: {score_str}")

        # Fallback if parsing fails - ALWAYS return a dictionary
        logging.warning(f"Could not parse AI auto-fill response, using default")
        fallback_status = 'absent' if is_entry else 'on_time'
        fallback_score = 0.0 if is_entry else 1.0

        return {
            'status': fallback_status,
            'score': fallback_score,
            'reason': 'auto_fill_parse_error_using_default'
        }

    def auto_fill_missing_sessions(self, student_id, last_session_num, current_session_num, student_name,
                                   is_entry):
        """ Auto fill the session before the first entry
        and the session between the last entry and the nearest exist"""
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                filled_sessions = []
                current_date = datetime.now().strftime('%Y-%m-%d')
                # #Get the last session_num from database
                # cursor.execute("""
                #     SELECT MAX(CAST(session_number AS INTEGER))
                #     FROM attendance_sessions
                #     WHERE student_id = ? AND session_date = ?
                # """, (student_id, current_date))
                # result = cursor.fetchone()
                # If none session, default to 0
                # last_session_num = result[0] if result[0] else 0
                print(f"Last session num was: {last_session_num}")
                print(f"current session num was: {current_session_num}")

                for session_num in range(last_session_num + 1, current_session_num):
                    session_info = get_session_by_number(session_num)
                    print(f"Checking session {session_num}, filled_sessions: {filled_sessions}")
                    if session_info:
                        auto_fill_result = self.calculate_auto_fill_score(student_id, session_num, student_name,
                                                                          is_entry)

                        # Use the dictionary values correctly
                        status = auto_fill_result['status']
                        score = auto_fill_result['score']
                        reason = auto_fill_result['reason']

                        cursor.execute("""
                              INSERT INTO attendance_sessions 
                              (student_id, session_date, entry_time, status, attendance_status, 
                               session_number, reason_for_scoring,attendance_score, late_minutes)
                              VALUES (?, ?, ?, ?, ?, ?, 
                                     ?,?, 0)
                          """, (
                            student_id, current_date,
                            datetime.now().strftime('%H:%M:%S'),
                            "present" if status != "absent" and is_entry is True else "left",
                            status,
                            session_num,
                            f"AUTO_FILLED: {reason} (score:{score})",
                            score
                        ))
                        filled_sessions.append({
                            'session': session_num,
                            'status': status,
                            'score': score,
                            'reason': reason
                        })

                        logging.info(
                            f"Auto-filled session {session_num} for {student_name}, ID: {student_id} with status '"
                            f"{status}' and score {score}")

                conn.commit()
                return filled_sessions

        except Exception as e:
            logging.error(f"Auto fill score failed: {e}")
            return []

    def record_entry(self, name, active_session=None):
        """Recording Entry. Note: the none values are just for debugging"""
        try:
            student_id = get_or_create_student(name)
            if student_id is None:
                return None
            with self.connection as conn:
                cursor = conn.cursor()
                current_datetime = datetime.now()
                current_date = current_datetime.strftime('%Y-%m-%d')
                current_time = current_datetime.time()
                session_info = get_current_session_direct()
                # Find the last exit_time
                cursor.execute("""
                      SELECT exit_time
                      FROM attendance_sessions
                      WHERE student_id = ? AND session_date = ? AND exit_time IS NOT NULL
                      ORDER BY exit_time DESC
                      LIMIT 1
                  """, (student_id, current_date))

                result = cursor.fetchone()
                if result and result[0] is not None:
                    # Convert string to time object
                    last_exit_time_str = result[0]
                    last_exit_time = datetime.strptime(last_exit_time_str, '%H:%M:%S').time()
                else:
                    last_exit_time = None

                if active_session is not None:
                    if isinstance(active_session, int):
                        session_info = get_session_by_number(active_session)
                    else:
                        session_info = active_session
                    print(f"After override: Session {session_info}")

                if not session_info:
                    logging.warning("No active session found")
                    return None

                # Get the session number from the last exit time
                if last_exit_time is not None:
                    last_session_info = get_current_session_with_time(last_exit_time)
                    last_session_num = last_session_info['session_number'] if isinstance(last_session_info,
                                                                                         dict) else 0
                else:
                    last_session_num = 0

                # If last lession_num is zero -> first_entry

                current_session_num = session_info['session_number']

                # Not allowing a second entry
                if last_session_num == current_session_num:
                    return None

                # Auto filling for entry
                self.auto_fill_missing_sessions(student_id, last_session_num, current_session_num, name, True)

                # To rework from here!!

                late_minutes = calculate_late_minutes(current_time, session_info['start_time'])

                # Get circumstances for THIS specific session
                student_history = get_student_attendance_history(student_id)
                student_circumstances = get_student_circumstances(student_id, session_info['session_number'])

                ai_prompt = f"""
                  ATTENDANCE DECISION MAKING:

                  STUDENT PROFILE:
                  - Name: {name} (ID: {student_id})
                  - Current Time: {current_time}
                  - Session: {session_info['session_number']} ({session_info['start_time']}-{session_info['end_time']})
                  - Late by: {late_minutes} minutes

                  HISTORICAL CONTEXT:
                  {student_history}

                  PERSONAL CIRCUMSTANCES:
                  {student_circumstances}

                  DECISION MATRIX (STRICT RULES - FOLLOW EXACTLY):
                  - 'on_time' (score: 1.0): Arrived within 5 minutes of session start
                  - 'late' (score: 0.1-0.9): Arrived 5-60 minutes late, adjust score based on circumstances
                  - 'absent' (score: 0.0): Arrived 60+ minutes late OR no valid circumstances for extreme lateness
                  - 'excused' (score: 1.0): Has valid documented excuse for this specific session

                  EXCUSE RULES:
                  • Use 'excused' ONLY if circumstances specifically mention this session number
                  • 'full' excuse type = completely excused regardless of arrival time
                  • 'late_arrival' excuse type = excused for being late to this session

                  SCORING GUIDELINES FOR 'late' STATUS:
                  • 0.8-0.9: 5-15 min late with valid circumstances
                  • 0.6-0.7: 15-30 min late with mitigating factors  
                  • 0.4-0.5: 30-45 min late with minor circumstances
                  • 0.1-0.3: 45-60 min late with weak or no valid reasons

                  Return ONLY: status,score,reason_for_scoring
                  Valid Examples:
                  on_time,1.0,arrived_within_5_minute_grace_period
                  late,0.8,15_min_late_due_to_documented_medical_appointment
                  excused,1.0,has_medical_excuse_for_session_3
                  absent,0.0,75_min_late_no_valid_circumstances

                  Your decision (ONLY use 'on_time', 'late', 'absent', or 'excused'):
                  """
                ai_response = self.llm.invoke(ai_prompt).content.strip()
                print(ai_response)
                # Parsing and checking for error
                parsed_values = parse_ai_response(ai_response, 3)
                if not parsed_values:
                    logging.warning(f"Failed to parse AI response: {ai_response}, using fallback")
                    if late_minutes <= 5:
                        status, score, reason_for_scoring = 'on_time', 1.0, 'fallback_grace_period'
                    elif late_minutes <= 60:
                        status, score, reason_for_scoring = 'late', max(0.1, 1.0 - (
                                late_minutes / 60)), 'fallback_late'
                    else:
                        status, score, reason_for_scoring = 'absent', 0.0, 'fallback_absent'
                else:
                    status, score, reason_for_scoring = parsed_values
                # Constraints
                allowed_statuses = ['on_time', 'late', 'absent', 'excused']
                if status not in allowed_statuses:
                    logging.warning(f"AI returned invalid status: {status}, defaulting to 'late'")
                    status = 'late'

                attendance_status = status
                attendance_score = float(score)
                ai_reason = reason_for_scoring

                if late_minutes > 0:
                    logging.warning(f"{name} is LATE by {late_minutes} minutes!")
                    print(f"\n{'=' * 80}")
                    print(f" AI ATTENDANCE DECISION ENGINE")
                    print(f"{'=' * 80}")
                    print(f" Student: {name} (ID: {student_id})")
                    print(f" Scheduled: {session_info['start_time']}")
                    print(f" Arrived: {current_time.strftime('%H:%M:%S')}")
                    print(f"⚠  Late by: {late_minutes} minutes")
                    print(f" Historical Pattern: {student_history}")
                    print(f" Personal Circumstances: {student_circumstances}")
                    print(f" AI Decision: {attendance_status}")
                    print(f" AI Score: {attendance_score}")
                    print(f" Reason for Scoring: {ai_reason}")
                    print(f"{'=' * 80}\n")
                else:
                    logging.info(f"{name} - AI Decision: {attendance_status}")
                    print(f"\n{'=' * 60}")
                    print(f"ATTENDANCE CONFIRMED")
                    print(f"{'=' * 60}")
                    print(f"Student: {name}")
                    print(f"Status: {attendance_status}")
                    print(f"Score: {attendance_score}")
                    print(f"Reason: {ai_reason}")
                    print(f"{'=' * 60}\n")

                # Store only time in entry_time, not full datetime
                cursor.execute("""
                      INSERT INTO attendance_sessions 
                      (student_id, session_date, entry_time, status, attendance_status, late_minutes, reason_for_scoring
                      ,attendance_score, session_number)
                      VALUES (?, ?, ?, 'present', ?, ?, ?,?, ?)
                  """, (
                    student_id,
                    current_date,  # Date goes here
                    current_time.strftime('%H:%M:%S'),
                    attendance_status,
                    late_minutes,
                    ai_reason,
                    attendance_score,
                    session_info['session_number']  # ADD session_number
                ))

                session_id = cursor.lastrowid
                conn.commit()

                logging.info(f" AI attendance recorded for {name}: {attendance_status} - {ai_reason}")

                return {
                    'session_id': session_id,
                    'student_id': student_id,
                    'status': attendance_status,
                    'score': attendance_score,
                    'late_minutes': late_minutes,
                    'reason_for_scoring': ai_reason,
                    'timestamp': current_datetime,
                    'circumstances_considered': student_circumstances,
                    'historical_context': student_history
                }
        except Exception as e:
            print(e)
            return None

    def record_exit(self, name, active_session=None, early_departure_reason=None):
        """Record exit with auto-filling. Note: the none values are just for debugging"""
        try:
            student_id = get_or_create_student(name)
            if student_id is None:
                return None
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                current_date = datetime.now().strftime('%Y-%m-%d')
                current_time = datetime.now().time()
                session_info = get_current_session_direct()

                # Find the last entry time for auto filling
                cursor.execute("""
                    SELECT entry_time, session_number
                    FROM attendance_sessions
                    WHERE student_id = ? AND session_date = ?
                    ORDER BY session_number DESC, entry_time DESC
                    LIMIT 1
                """, (student_id, current_date))

                result = cursor.fetchone()

                if result and result[0] is not None:
                    # Convert string to time object
                    last_entry_time_str = result[0]
                    current_session_id = result[1]  # Get the session ID for the UPDATE
                    last_entry_time = datetime.strptime(last_entry_time_str, '%H:%M:%S').time()
                else:
                    last_entry_time = None
                    current_session_id = None
                print(last_entry_time)
                if active_session is not None:
                    if isinstance(active_session, int):
                        session_info = get_session_by_number(active_session)
                    else:
                        session_info = active_session

                if not session_info:
                    logging.warning("The class has already ended!!")
                    return None

                # Get the session number from the last entry time
                if last_entry_time is not None:
                    last_session_info = get_current_session_with_time(last_entry_time)
                    last_session_num = last_session_info['session_number'] if isinstance(last_session_info, dict) else 0
                else:
                    last_session_num = 0

                current_session_num = session_info["session_number"]

                # Auto filling for exit
                self.auto_fill_missing_sessions(student_id, last_session_num, current_session_num, name,
                                                False)  # Not an entry

                # Calculating score part
                entry_time = last_entry_time
                current_datetime = datetime.now()
                entry_datetime = datetime.combine(current_datetime.date(), entry_time)

                # Early leaving duration
                duration_minutes = max(1, int((current_datetime - entry_datetime).total_seconds() / 60))
                session_end_time = session_info['end_time']
                early_departure_minutes = 0

                if current_time < session_end_time:
                    end_dt = datetime.combine(current_datetime.date(), session_end_time)
                    early_departure_minutes = max(0, int((end_dt - current_datetime).total_seconds() / 60))

                student_history = get_student_attendance_history(student_id)
                student_circumstances = get_student_circumstances(student_id, session_info['session_number'])

                ai_prompt = f"""
                EARLY DEPARTURE PENALTY CALCULATION:

                STUDENT: {name}
                SESSION: {session_info['session_number']} ({session_info['start_time']}-{session_info['end_time']})
                EARLY DEPARTURE: {early_departure_minutes} minutes early
                REASON: {early_departure_reason or 'Not specified'}

                HISTORICAL PATTERNS:
                {student_history}

                CIRCUMSTANCES:
                {student_circumstances}

                PENALTY MATRIX:
                - 0-5 min early: 10% penalty (score: 0.9)
                - 6-15 min early: 30% penalty (score: 0.7)  
                - 16-30 min early: 60% penalty (score: 0.4)
                - 31+ min early: 90% penalty (score: 0.1)
                - Medical/emergency: No penalty (score: 1.0)
                - Pre-approved: Reduced penalty

                IMPORTANT: Respond ONLY in this exact format: final_score,penalty_reason
                - final_score: number between 0.1 and 1.0
                - penalty_reason: short_description_without_spaces

                Examples:
                0.7,left_12_minutes_early_30_percent_penalty
                1.0,medical_appointment_no_penalty
                0.4,left_25_minutes_early_60_percent_penalty
                0.9,left_3_minutes_early_10_percent_penalty

                Do NOT include any explanations, just the score and reason separated by comma.

                Your response:
                """

                ai_response = self.llm.invoke(ai_prompt).content.strip()

                # Parsing
                final_score, penalty_reason = parse_ai_response(ai_response, 2)
                try:
                    final_score_float = float(final_score)
                except ValueError:
                    final_score_float = 0.7  # Default fallback

                cursor.execute("""
                    UPDATE attendance_sessions
                    SET exit_time = ?, 
                        duration_minutes = ?,
                        status = 'left',
                        attendance_status = 'left_early',
                        reason_for_scoring = ?,
                        attendance_score = ?
                    WHERE student_id = ? AND session_date = ? AND session_number = ?
                """, (
                    current_time.strftime('%H:%M:%S'),
                    duration_minutes,
                    f"EARLY_EXIT: {penalty_reason} (final_score:{final_score})",
                    final_score,
                    student_id,
                    current_date,
                    current_session_num
                ))

                conn.commit()

                # Display penalty analysis
                print(f"\n{'=' * 70}")
                print(f"⚠️  EARLY DEPARTURE PENALTY ANALYSIS")
                print(f"{'=' * 70}")
                print(f"Student: {name}")
                print(f"Session: {session_info['session_number']}")
                print(f"Duration: {duration_minutes}/45 minutes")
                print(f"Early Departure: {early_departure_minutes} minutes")
                print(f"Final Score: {final_score}")
                print(f"Penalty Reason: {penalty_reason}")
                print(f"{'=' * 70}\n")

                logging.info(f"⚠️ Early departure penalty for {name}: {final_score} - {penalty_reason}")

                return {
                    'student_id': student_id,
                    'duration_minutes': duration_minutes,
                    'early_departure_minutes': early_departure_minutes,
                    'final_score': float(final_score),
                    'penalty_reason': penalty_reason,
                    'auto_filled_sessions': True
                }

        except Exception as e:
            logging.error(f"Error in recording exit: {e}")
            return None
