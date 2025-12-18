import sqlite3

# Check agent database
print("=== AGENT DATABASE ===")
conn = sqlite3.connect('face-reidentification/agent/attendance.db')
cursor = conn.cursor()

# Count attendance sessions
cursor.execute('SELECT COUNT(*) FROM attendance_sessions')
print(f"Attendance sessions: {cursor.fetchone()[0]}")

# Get students
cursor.execute('SELECT * FROM students LIMIT 5')
students = cursor.fetchall()
print(f"Students (first 5): {students}")

# Get column names
cursor.execute('PRAGMA table_info(students)')
columns = cursor.fetchall()
print(f"Students table columns: {[col[1] for col in columns]}")

conn.close()

print("\n=== MAIN DATABASE ===")
conn2 = sqlite3.connect('face-reidentification/database/attendance.db')
cursor2 = conn2.cursor()

# Count attendance sessions
cursor2.execute('SELECT COUNT(*) FROM attendance_sessions')
print(f"Attendance sessions: {cursor2.fetchone()[0]}")

# Get students
cursor2.execute('SELECT id, first_name, last_name FROM students LIMIT 5')
students2 = cursor2.fetchall()
print(f"Students (first 5): {students2}")

conn2.close()
