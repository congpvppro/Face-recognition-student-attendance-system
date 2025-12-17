import sys
import os
import signal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ApprovalAgent import ApprovalAgent

RUNNING = True
import certifi
from dotenv import load_dotenv

# Set SSL certificate for HTTPS connections
os.environ["SSL_CERT_FILE"] = certifi.where()

import schedule
import time
import threading

load_dotenv()


def signal_handler(signum, frame):
    global RUNNING
    print(f"\nStopping scheduler...")
    RUNNING = False


def daily_approval():
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting circumstance validation...")

    agent = ApprovalAgent()

    agent.validate_circumstance()

    print(f"[{time.strftime('%H:%M:%S')}] Validation complete")


def start_scheduler():
    global RUNNING
    RUNNING = True

    print("\nConfigure Approval Agent Run Time")
    print("=" * 40)
    print("Default time: 07:00 AM (press Enter to use default)")
    print("Or enter custom time (24-hour format, e.g., 09:30)")

    time_str = input("Run time (HH:MM) [default 07:00]: ").strip()

    if not time_str:
        time_str = "07:00"

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

        print("Invalid time. Please enter in HH:MM format (e.g., 09:30)")
        time_str = input("Run time (HH:MM): ").strip()

    schedule.clear()
    schedule.every().day.at(time_str).do(daily_approval)

    print(f"\nApproval Agent configured to run daily at {time_str}")
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
    print("\nRunning circumstance validation now...")
    daily_approval()


def main():
    global RUNNING

    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 40)
    print("CIRCUMSTANCE APPROVAL AGENT")
    print("=" * 40)
    print("1. Run validation now")
    print("2. Start scheduler (default: 07:00 AM)")
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


def run_daily_approval():
    """Run the daily approval task"""
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting daily circumstance validation...")
    try:
        agent = ApprovalAgent()
        agent.validate_circumstance()
        print(f"[{time.strftime('%H:%M:%S')}] Validation complete")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Validation error: {e}")


def start_approval_scheduler(time_str="07:00"):
    """
    Start the scheduler in background thread
    """
    os.environ["SSL_CERT_FILE"] = certifi.where()
    load_dotenv()
    schedule.clear()
    schedule.every().day.at(time_str).do(run_daily_approval)

    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(60)

    # Start in background thread
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    print(f"Approval scheduler started. Daily at {time_str}")

    return thread
