from Utility import get_connection
from datetime import datetime
from sqlite3 import Error

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from sqlite3 import Error
from dotenv import load_dotenv
from langchain_groq import ChatGroq


class ApprovalAgent:
    def __init__(self):
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        load_dotenv()
        self.llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"),
                            model_name="openai/gpt-oss-120b",
                            temperature=0)

    def get_unchecked_circumstances(self):
        """
        Get students and their circumstances that need validation
        Returns: dict with 'student_ids' and 'circumstances' lists
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT student_id, circumstance
                FROM pending_circumstances
                WHERE validated = 0
                """)
                results = cursor.fetchall()

                # Organize into parallel lists
                student_ids = [row[0] for row in results]
                circumstances = [row[1] for row in results]

                return {
                    'student_ids': student_ids,
                    'circumstances': circumstances
                }
        except Error as e:
            print(e)
            return None

    def validate_circumstance(self):
        """
        Validate student circumstances using LLM and insert valid ones into database
        """
        unchecked_data = self.get_unchecked_circumstances()

        if not unchecked_data or not unchecked_data['student_ids']:
            print("No circumstances to validate")
            return

        student_ids = unchecked_data['student_ids']
        circumstances = unchecked_data['circumstances']
        start_dates = unchecked_data['start_date']
        end_dates = unchecked_data['end_date']

        # Build the circumstances list for the prompt
        circumstances_text = ""
        for i, (student_id, circumstance, start_date, end_date) in enumerate(
                zip(student_ids, circumstances, start_dates, end_dates), 1):
            circumstances_text += f"{i}. Student ID: {student_id} - Circumstance: {circumstance} (Period: {start_date} to {end_date})\n"

            prompt = f"""You are validating student circumstances for academic records. Analyze the following {len(circumstances)} circumstances and determine which ones are valid and legitimate.
            
            Circumstances to validate:
            {circumstances_text}
            
            Valid circumstances typically include:
            - Medical emergencies or health issues
            - Family emergencies (death, serious illness)
            - Natural disasters or accidents
            - Mental health crises
            - Financial hardships affecting studies
            - Technical issues preventing submission
            - Other legitimate academic barriers
            
            Invalid circumstances include:
            - Vague excuses without details
            - Poor time management
            - Simple forgetfulness
            - Non-emergency personal preferences
            - Circumstances that don't affect academic performance
            
            Return ONLY a JSON array of valid circumstances in this exact format:
            [
              {{"student_id": 123, "circumstance": "the circumstance text", "start_date": "2024-01-15", "end_date": "2024-01-20"}},
              {{"student_id": 456, "circumstance": "the circumstance text", "start_date": "2024-02-01", "end_date": "2024-02-05"}}
            ]
            
            Return an empty array [] if none are valid. Do not include any other text or explanation."""

            response = self.llm.invoke(prompt)
            analysis_text = response.content.strip()

            # Parse JSON response
            import json
            try:
                # Remove markdown code blocks if present
                if analysis_text.startswith("```"):
                    analysis_text = analysis_text.split("```")[1]
                    if analysis_text.startswith("json"):
                        analysis_text = analysis_text[4:]
                    analysis_text = analysis_text.strip()

                valid_circumstances = json.loads(analysis_text)

                # Insert valid circumstances into database
                if valid_circumstances:
                    self._insert_valid_circumstances(valid_circumstances)
                    print(f"Inserted {len(valid_circumstances)} valid circumstances")
                else:
                    print("No valid circumstances found")

            except json.JSONDecodeError as e:
                print(f"Error parsing LLM response: {e}")
                print(f"Response was: {analysis_text}")

    def _insert_valid_circumstances(self, valid_circumstances):
        """
        Insert validated circumstances into student_circumstances table
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                for item in valid_circumstances:
                    cursor.execute("""
                    INSERT INTO student_circumstances (student_id, circumstance, created_at)
                    VALUES (?, ?, datetime('now'))
                    """, (item['student_id'], item['circumstance']))

                conn.commit()
                print(f"Successfully inserted {len(valid_circumstances)} circumstances")

        except Error as e:
            print(f"Database error: {e}")
            conn.rollback()