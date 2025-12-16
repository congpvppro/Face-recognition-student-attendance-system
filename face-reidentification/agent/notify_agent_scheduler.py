# agent/notify_scheduler.py
import schedule
import time
import threading
from datetime import datetime
from agent.NotifyAgent import NotifyAgent
from agent.Utility import get_connection



def run_notifications():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running attendance notifications...")
    try:
        NotifyAgent().notify_missing_students()
    except Exception as e:
        print(f"[NotifyScheduler] Error: {e}")



def get_session_schedule():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_number, start_time
                FROM class_schedule
                ORDER BY session_number
            """)
            rows = cursor.fetchall()
            return {r[0]: r[1] for r in rows}
    except Exception:
        # fallback
        return {
            1: "07:20",
            2: "08:10",
            3: "09:00",
            4: "09:55",
            5: "10:45",
        }


def start_notify_scheduler(delay_minutes=5):
    """
    Start attendance notification scheduler in background thread.
    Safe to call from main application.
    """

    schedule.clear()
    sessions = get_session_schedule()

    for session_num, start_time in sessions.items():
        schedule.every().day.at(start_time).do(
            _run_with_delay, delay_minutes
        )
        print(f"[NotifyScheduler] Session {session_num} scheduled at {start_time} (+{delay_minutes} min)")

    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(30)

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()

    print("[NotifyScheduler] Background scheduler started")
    return thread


def _run_with_delay(delay_minutes):
    threading.Timer(delay_minutes * 60, run_notifications).start()
