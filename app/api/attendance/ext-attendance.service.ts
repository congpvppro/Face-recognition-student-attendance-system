import Database from "bun:sqlite";
import { existsSync } from "fs";
import { NotFoundError } from "@common/errors/httpErrors";
import {
  ATTENDANCE_DB_PATHS,
  USERS_DB_PATHS,
  type AttendanceStatus,
} from "@common/config";

// Attendance record type from Python DB
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
 * Resolves the first existing path from a list of possible paths
 */
function resolveDbPath(possiblePaths: string[], defaultPath: string): string {
  for (const p of possiblePaths) {
    if (existsSync(p)) {
      return p;
    }
  }
  console.warn(
    `Could not find DB in common paths, defaulting to: ${defaultPath}`,
  );
  return defaultPath;
}

/**
 * Service to connect to the external Python agent's attendance database
 */
export class ExtAttendanceService {
  private db: Database;
  private dbPath: string;

  constructor() {
    this.dbPath = resolveDbPath(
      ATTENDANCE_DB_PATHS,
      "face-reidentification/agent/attendance.db",
    );

    try {
      this.db = new Database(this.dbPath, { readonly: true });
    } catch (e) {
      console.error(
        `Failed to connect to external attendance database at ${this.dbPath}`,
        e,
      );
      throw new Error("External attendance database not found.");
    }
  }

  /**
   * Get the main users database connection
   */
  private getMainDb(): Database {
    const mainDbPath = resolveDbPath(USERS_DB_PATHS, "users.sqlite");
    return new Database(mainDbPath, { readonly: true });
  }

  /**
   * Get all attendance records for a specific class on a specific date
   */
  public getAttendanceByClassAndDate(
    classId: number,
    date: string,
  ): AttendanceRecord[] {
    const mainDb = this.getMainDb();

    try {
      const studentIdsQuery = mainDb.query<
        { id: string },
        { $class_id: number }
      >("SELECT id FROM students WHERE class_id = $class_id");
      const studentsInClass = studentIdsQuery.all({ $class_id: classId });
      const studentIds = studentsInClass.map((s) => s.id);

      if (studentIds.length === 0) {
        return [];
      }

      // The Python DB uses 'name' field which corresponds to student ID from main DB
      const placeholders = studentIds.map(() => "?").join(",");
      const query = this.db.query<AttendanceRecord, unknown[]>(`
        SELECT
          s.name as student_id,
          a.session_date,
          a.entry_time,
          a.exit_time,
          a.attendance_status,
          a.late_minutes,
          a.session_number
        FROM attendance_sessions a
        JOIN students s ON a.student_id = s.id
        WHERE a.session_date = ? AND s.name IN (${placeholders})
      `);

      return query.all(date, ...studentIds);
    } finally {
      mainDb.close();
    }
  }

  /**
   * Get all attendance records for a specific student
   */
  public getAttendanceByStudent(studentId: string): AttendanceRecord[] {
    const query = this.db.query<AttendanceRecord, { $studentId: string }>(`
      SELECT
        s.name as student_id,
        a.session_date,
        a.entry_time,
        a.exit_time,
        a.attendance_status,
        a.late_minutes,
        a.session_number
      FROM attendance_sessions a
      JOIN students s ON a.student_id = s.id
      WHERE s.name = $studentId
      ORDER BY a.session_date DESC, a.session_number ASC
    `);

    return query.all({ $studentId: studentId });
  }

  /**
   * Get or create a student in the Python DB by name/ID
   */
  private getOrCreateStudent(
    writeDb: Database,
    studentId: string,
  ): { id: number } {
    // Try to find existing student
    const studentQuery = writeDb.query<{ id: number }, { $name: string }>(
      "SELECT id FROM students WHERE name = $name",
    );
    let student = studentQuery.get({ $name: studentId });

    if (!student) {
      // Create the student in Python DB
      const insertQuery = writeDb.query<{ id: number }, { $name: string }>(
        "INSERT INTO students (name) VALUES ($name) RETURNING id",
      );
      student = insertQuery.get({ $name: studentId });

      if (!student) {
        throw new Error(`Failed to create student ${studentId} in external DB`);
      }
    }

    return student;
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
    // Open a write connection for this operation
    const writeDb = new Database(this.dbPath);

    try {
      // Get or create student in Python DB
      const student = this.getOrCreateStudent(writeDb, studentId);

      // Check if attendance record exists
      const existingQuery = writeDb.query<
        { id: number },
        { $student_id: number; $date: string; $session: number }
      >(`
        SELECT id FROM attendance_sessions
        WHERE student_id = $student_id AND session_date = $date AND session_number = $session
      `);
      const existing = existingQuery.get({
        $student_id: student.id,
        $date: date,
        $session: session,
      });

      if (existing) {
        // Update existing record
        const updateQuery = writeDb.query(`
          UPDATE attendance_sessions
          SET attendance_status = $status
          WHERE id = $id
        `);
        updateQuery.run({
          $status: status,
          $id: existing.id,
        });
      } else {
        // Insert new record
        const insertQuery = writeDb.query(`
          INSERT INTO attendance_sessions (
            student_id, session_date, session_number,
            entry_time, attendance_status, late_minutes
          ) VALUES (
            $student_id, $date, $session,
            $entry_time, $status, $late_minutes
          )
        `);
        insertQuery.run({
          $student_id: student.id,
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
      console.error("Failed to update external attendance DB", e);
      throw new Error("Failed to update external attendance record.");
    } finally {
      writeDb.close();
    }
  }

  /**
   * Close the database connection
   */
  public close(): void {
    this.db.close();
  }
}
