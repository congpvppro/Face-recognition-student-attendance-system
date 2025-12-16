import { NotFoundError } from "@common/errors/httpErrors";
import { db } from "@user/sqlite";
import {
  ExtAttendanceService,
  type AttendanceRecord,
} from "./ext-attendance.service";

export interface AttendanceFilters {
  classId?: number;
  date?: string;
}

/**
 * Service for managing attendance records
 * Relies on the Python agent's database for attendance data
 */
export class AttendanceService {
  private extAttendanceService: ExtAttendanceService;

  constructor() {
    this.extAttendanceService = new ExtAttendanceService();
  }

  /**
   * Verify that a student exists in the main database
   */
  private verifyStudentExists(studentId: string): void {
    const studentQuery = db.query<{ id: string }, { $id: string }>(
      "SELECT id FROM students WHERE id = $id",
    );
    const student = studentQuery.get({ $id: studentId });

    if (!student) {
      throw new NotFoundError(`Student with ID '${studentId}' not found.`);
    }
  }

  /**
   * Verify that a class exists in the main database
   */
  private verifyClassExists(classId: number): void {
    const classQuery = db.query<{ id: number }, { $id: number }>(
      "SELECT id FROM classes WHERE id = $id",
    );
    const course = classQuery.get({ $id: classId });

    if (!course) {
      throw new NotFoundError(`Class with ID ${classId} not found.`);
    }
  }

  /**
   * Get attendance records based on filters
   * Requires both classId and date for the Python DB query
   */
  public getAttendance(filters: AttendanceFilters): AttendanceRecord[] {
    if (filters.classId && filters.date) {
      try {
        return this.extAttendanceService.getAttendanceByClassAndDate(
          filters.classId,
          filters.date,
        );
      } catch (error) {
        console.error("Failed to fetch from external DB:", error);
        return [];
      }
    }

    // Python DB is optimized for class+date queries
    // Return empty array if filters are insufficient
    return [];
  }

  /**
   * Get all attendance records for a specific student
   */
  public getAttendanceByStudent(studentId: string): AttendanceRecord[] {
    return this.extAttendanceService.getAttendanceByStudent(studentId);
  }

  /**
   * Update the attendance status for a student
   */
  public updateAttendanceStatus(
    studentId: string,
    date: string,
    session: number,
    status: string,
  ): { message: string } {
    return this.extAttendanceService.updateAttendanceStatus(
      studentId,
      date,
      session,
      status,
    );
  }
}
