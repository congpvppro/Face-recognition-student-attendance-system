import Database from "bun:sqlite";
import { NotFoundError } from "@common/errors/httpErrors";
import { type AttendanceStatus } from "@common/config";
import { db, dbPath } from "@user/sqlite";

// Attendance record type from unified DB
export interface AttendanceRecord {
  student_id: string;
  session_date: string;
  entry_time: string | null;
  exit_time: string | null;
  attendance_status: AttendanceStatus;
  late_minutes: number;
  session_number: number;
}

/**
 * Service for attendance operations using the unified database
 */
export class ExtAttendanceService {
  constructor() {
    // Uses the unified database from sqlite.ts
  }

  /**
   * Get all attendance records for a specific class on a specific date
   */
  public getAttendanceByClassAndDate(
    classId: number,
    date: string,
  ): AttendanceRecord[] {
    const studentIdsQuery = db.query<{ id: string }, { $class_id: number }>(
      "SELECT id FROM students WHERE class_id = $class_id",
    );
    const studentsInClass = studentIdsQuery.all({ $class_id: classId });
    const studentIds = studentsInClass.map((s) => s.id);

    if (studentIds.length === 0) {
      return [];
    }

    // Query attendance using student IDs
    const placeholders = studentIds.map(() => "?").join(",");
    const query = db.query<AttendanceRecord, unknown[]>(`
      SELECT
        s.id as student_id,
        a.session_date,
        a.entry_time,
        a.exit_time,
        a.attendance_status,
        a.late_minutes,
        a.session_number
      FROM attendance_sessions a
      JOIN students s ON CAST(a.student_id AS TEXT) = s.id
      WHERE a.session_date = ? AND s.id IN (${placeholders})
    `);

    return query.all(date, ...studentIds);
  }

  /**
   * Get all attendance records for a specific student
   */
  public getAttendanceByStudent(studentId: string): AttendanceRecord[] {
    const query = db.query<AttendanceRecord, { $studentId: string }>(`
      SELECT
        s.id as student_id,
        a.session_date,
        a.entry_time,
        a.exit_time,
        a.attendance_status,
        a.late_minutes,
        a.session_number
      FROM attendance_sessions a
      JOIN students s ON CAST(a.student_id AS TEXT) = s.id
      WHERE s.id = $studentId
      ORDER BY a.session_date DESC, a.session_number ASC
    `);

    return query.all({ $studentId: studentId });
  }

  /**
   * Get student by ID, returns the internal numeric ID for attendance_sessions
   */
  private getStudentInternalId(studentId: string): number {
    // First try to find by string ID
    const studentQuery = db.query<{ rowid: number }, { $id: string }>(
      "SELECT rowid FROM students WHERE id = $id",
    );
    const student = studentQuery.get({ $id: studentId });

    if (student) {
      return student.rowid;
    }

    throw new NotFoundError(`Student with ID ${studentId} not found`);
  }

  /**
   * Manually update or create an attendance record
   * Uses UPSERT logic to handle cases where no record exists yet
   */
  public updateAttendanceStatus(
    studentId: string,
    date: string,
    session: number,
    status: string,
  ): { message: string } {
    try {
      // Get the student's internal ID (rowid) for attendance_sessions table
      // The attendance_sessions table uses INTEGER student_id that matches rowid
      const studentQuery = db.query<{ id: string }, { $id: string }>(
        "SELECT id FROM students WHERE id = $id",
      );
      const student = studentQuery.get({ $id: studentId });

      if (!student) {
        throw new NotFoundError(`Student with ID ${studentId} not found`);
      }

      // Check if attendance record exists
      const existingQuery = db.query<
        { id: number },
        { $student_id: string; $date: string; $session: number }
      >(`
        SELECT id FROM attendance_sessions
        WHERE CAST(student_id AS TEXT) = $student_id AND session_date = $date AND session_number = $session
      `);
      const existing = existingQuery.get({
        $student_id: studentId,
        $date: date,
        $session: session,
      });

      if (existing) {
        // Update existing record
        const updateQuery = db.query(`
          UPDATE attendance_sessions
          SET attendance_status = $status
          WHERE id = $id
        `);
        updateQuery.run({
          $status: status,
          $id: existing.id,
        });
      } else {
        // Insert new record - use the string student ID cast to integer
        const insertQuery = db.query(`
          INSERT INTO attendance_sessions (
            student_id, session_date, session_number,
            entry_time, attendance_status, late_minutes
          ) VALUES (
            CAST($student_id AS INTEGER), $date, $session,
            $entry_time, $status, $late_minutes
          )
        `);
        insertQuery.run({
          $student_id: studentId,
          $date: date,
          $session: session,
          $entry_time:
            status === "absent"
              ? null
              : new Date().toTimeString().split(" ")[0],
          $status: status,
          $late_minutes: 0,
        });
      }

      return { message: "Attendance updated successfully" };
    } catch (e) {
      if (e instanceof NotFoundError) {
        throw e;
      }
      console.error("Failed to update attendance DB", e);
      throw new Error("Failed to update attendance record.");
    }
  }
}
