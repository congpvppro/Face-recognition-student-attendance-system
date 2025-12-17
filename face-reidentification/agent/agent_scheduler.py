
import sys
import os
import signal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from AnalysisAgent import AnalysisAgent

RUNNING = True
import certifi
from dotenv import load_dotenv

# Set SSL certificate for HTTPS connections
os.environ["SSL_CERT_FILE"] = certifi.where()
print("SSL_CERT_FILE set to:", os.environ["SSL_CERT_FILE"])

import schedule
import time
import threading
from AnalysisAgent import AnalysisAgent

load_dotenv()

def signal_handler(signum, frame):
    global RUNNING
    print(f"\nStopping scheduler...")
    RUNNING = False


def daily_analysis():
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting analysis...")

    agent = AnalysisAgent()

    result1 = agent.generate_daily_insights()
    print(f"[{time.strftime('%H:%M:%S')}] Insights: {result1}")

    result2 = agent.evaluate_past_interventions()
    print(f"[{time.strftime('%H:%M:%S')}] Evaluated {result2} interventions")

    result3 = agent.analysis_student_problems()
    if result3:
        print(f"[{time.strftime('%H:%M:%S')}] Analyzed {len(result3)} students")
        for student in result3:
            print(f"  - {student['student_name']}: {student['alert_level']}")
    else:
        print(f"[{time.strftime('%H:%M:%S')}] No high-priority students")

    print(f"[{time.strftime('%H:%M:%S')}] Analysis complete")


def start_scheduler():
    global RUNNING
    RUNNING = True

    print("\nConfigure Agent Run Time")
    print("========================")
    print("Default time: 12:00 PM (press Enter to use default)")
    print("Or enter custom time (24-hour format, e.g., 14:30)")

    time_str = input("Run time (HH:MM) [default 12:00]: ").strip()

    if not time_str:
        time_str = "12:00"

    while True:
        try:
            if ":" in time_str and len(time_str.split(":")) == 2:
                hour, minute = time_str.split(":")
                hour = int(hour)
                minute = int(minute)
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    break
                else:
                    print("Hour must be 0-23, minute must be 0-59")
        except ValueError:
            pass

        print("Invalid time. Please enter in HH:MM format (e.g., 14:30)")
        time_str = input("Run time (HH:MM): ").strip()

    schedule.clear()
    schedule.every().day.at(time_str).do(daily_analysis)

    print(f"\nAgent configured to run daily at {time_str}")
    print(f"Next run: {schedule.next_run().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nScheduler running. Press Ctrl+C to stop.")

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while RUNNING:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    schedule.clear()
    print("\nScheduler stopped.")


def run_now():
    print("\nRunning analysis now...")
    daily_analysis()


def main():
    global RUNNING

    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 40)
    print("STUDENT ANALYSIS AGENT")
    print("=" * 40)
    print("1. Run analysis now")
    print("2. Start scheduler (default: 12:00 PM)")
    print("3. Exit")
    print("=" * 40)

    try:
        choice = input("\nChoose (1-3): ").strip()

        if choice == "1":
            run_now()
        elif choice == "2":
            start_scheduler()
        else:
            print("Goodbye!")
    except KeyboardInterrupt:
        print("\nExiting...")


def run_daily_analysis():
    """Run the daily analysis task"""
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting daily analysis...")
    try:
        agent = AnalysisAgent()

        result1 = agent.generate_daily_insights()
        print(f"[{time.strftime('%H:%M:%S')}] Insights generated")

        result2 = agent.evaluate_past_interventions()
        print(f"[{time.strftime('%H:%M:%S')}] Interventions evaluated")

        result3 = agent.analysis_student_problems()
        if result3:
            print(f"[{time.strftime('%H:%M:%S')}] Analyzed {len(result3)} students")

        print(f"[{time.strftime('%H:%M:%S')}] Analysis complete")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Analysis error: {e}")


def start_analysis_scheduler(time_str="12:00"):
    """Start the scheduler in background thread"""
    schedule.clear()
    schedule.every().day.at(time_str).do(run_daily_analysis)

    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    # Start in background thread
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    print(f"Analysis scheduler started. Daily at {time_str}")

    return thread

if __name__ == "__main__":
    main()