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
        a.student_id,
        a.session_date,
        a.entry_time,
        a.exit_time,
        a.attendance_status,
        a.late_minutes,
        a.session_number
      FROM attendance_sessions a
      WHERE a.session_date = ? AND a.student_id IN (${placeholders})
    `);

    return query.all(date, ...studentIds);
  }

  /**
   * Get all attendance records for a specific student
   */
  public getAttendanceByStudent(studentId: string): AttendanceRecord[] {
    const query = db.query<AttendanceRecord, { $studentId: string }>(`
      SELECT
        student_id,
        session_date,
        entry_time,
        exit_time,
        attendance_status,
        late_minutes,
        session_number
      FROM attendance_sessions
      WHERE student_id = $studentId
      ORDER BY session_date DESC, session_number ASC
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
        WHERE student_id = $student_id AND session_date = $date AND session_number = $session
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
        // Insert new record - student_id is TEXT type
        const insertQuery = db.query(`
          INSERT INTO attendance_sessions (
            student_id, session_date, session_number,
            entry_time, attendance_status, late_minutes
          ) VALUES (
            $student_id, $date, $session,
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

  /**
   * Export student attendance report for a class
   * Returns CSV content as string
   */
  public exportStudentReport(
    classId: number,
    date?: string,
  ): { content: string; filename: string } {
    // Get class name
    const classQuery = db.query<{ name: string }, { $id: number }>(
      "SELECT name FROM classes WHERE id = $id",
    );
    const classRow = classQuery.get({ $id: classId });
    const className = classRow?.name || `Class_${classId}`;

    // Get students in this class
    const studentsQuery = db.query<
      {
        id: string;
        name: string;
        first_name: string | null;
        last_name: string | null;
      },
      { $class_id: number }
    >(
      "SELECT id, name, first_name, last_name FROM students WHERE class_id = $class_id ORDER BY name",
    );
    const students = studentsQuery.all({ $class_id: classId });

    const headers = [
      "Mã HS",
      "Họ tên",
      "Tổng tiết",
      "Có mặt",
      "Vắng",
      "Muộn",
      "Tỷ lệ %",
      "Điểm TB",
    ];
    if (date) {
      headers.push("Ngày");
    }

    const rows: string[][] = [];

    for (const student of students) {
      const firstName = student.first_name || "";
      const lastName = student.last_name || "";
      let studentName = `${firstName} ${lastName}`.trim();
      if (!studentName) {
        studentName = student.name || student.id;
      }

      let statsQuery;
      let stats;

      if (date) {
        statsQuery = db.query<
          {
            total: number;
            attended: number;
            absent: number;
            late: number;
            avg_score: number | null;
          },
          { $student_id: string; $date: string }
        >(`
          SELECT
            COUNT(*) as total,
            SUM(CASE WHEN attendance_status IN ('on_time', 'late') THEN 1 ELSE 0 END) as attended,
            SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END) as absent,
            SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) as late,
            AVG(attendance_score) as avg_score
          FROM attendance_sessions
          WHERE student_id = $student_id AND session_date = $date
        `);
        stats = statsQuery.get({ $student_id: student.id, $date: date });
      } else {
        statsQuery = db.query<
          {
            total: number;
            attended: number;
            absent: number;
            late: number;
            avg_score: number | null;
          },
          { $student_id: string }
        >(`
          SELECT
            COUNT(*) as total,
            SUM(CASE WHEN attendance_status IN ('on_time', 'late') THEN 1 ELSE 0 END) as attended,
            SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END) as absent,
            SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) as late,
            AVG(attendance_score) as avg_score
          FROM attendance_sessions
          WHERE student_id = $student_id
        `);
        stats = statsQuery.get({ $student_id: student.id });
      }

      if (stats && stats.total > 0) {
        const attendancePct =
          Math.round((stats.attended / stats.total) * 1000) / 10;
        const avgScore = Math.round((stats.avg_score || 0) * 100) / 100;
        const row = [
          student.id,
          studentName,
          String(stats.total),
          String(stats.attended),
          String(stats.absent),
          String(stats.late),
          `${attendancePct}%`,
          String(avgScore),
        ];
        if (date) {
          row.push(date);
        }
        rows.push(row);
      } else {
        const row = [student.id, studentName, "0", "0", "0", "0", "0%", "0"];
        if (date) {
          row.push(date);
        }
        rows.push(row);
      }
    }

    // Build CSV content
    const csvRows = [headers.join(",")];
    for (const row of rows) {
      // Escape fields that contain commas or quotes
      const escapedRow = row.map((field) => {
        if (field.includes(",") || field.includes('"')) {
          return `"${field.replace(/"/g, '""')}"`;
        }
        return field;
      });
      csvRows.push(escapedRow.join(","));
    }

    const suffix = date ? `_${date}` : "_total";
    return {
      content: csvRows.join("\n"),
      filename: `student_report_${className}${suffix}.csv`,
    };
  }
}
