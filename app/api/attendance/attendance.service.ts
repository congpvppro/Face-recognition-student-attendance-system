import type { RecognitionResponseSchema } from "@attendance/attendance.model";
import { InternalServerError, NotFoundError } from "@common/errors/httpErrors";
import { db } from "@user/sqlite";
import type { Static } from "elysia";
import ky from "ky";

type RecognitionResponse = Static<typeof RecognitionResponseSchema>;

export class AttendanceService {
	constructor() {
		this.initDatabase();
	}

	private initDatabase() {
		db.run(`
      CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        class_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES students (id),
        FOREIGN KEY (class_id) REFERENCES classes (id)
      );
    `);
	}

	public async markAttendance(
		studentId: string,
		classId: number,
	): Promise<void> {
		// First, verify the student exists
		const studentQuery = db.query<{ id: string }, { $id: string }>(
			"SELECT id FROM students WHERE id = $id",
		);
		const student = studentQuery.get({ $id: studentId });

		if (!student) {
			throw new NotFoundError(`Student with ID '${studentId}' not found.`);
		}

		// Verify the class exists
		const classQuery = db.query("SELECT id FROM classes WHERE id = $id");
		const course = classQuery.get({ $id: classId });
		if (!course) {
			throw new NotFoundError(`Class with ID ${classId} not found.`);
		}

		// Insert an attendance record
		const attendanceQuery = db.query(
			"INSERT INTO attendance (user_id, class_id, timestamp) VALUES ($userId, $classId, $timestamp)",
		);
		const result = attendanceQuery.run({
			$userId: student.id,
			$classId: classId,
			$timestamp: new Date().toISOString(),
		});

		if (result.changes === 0) {
			throw new InternalServerError("Failed to mark attendance.");
		}
	}

	public getAttendance(
		filters: { classId?: number; date?: string },
		user?: any,
	): any[] {
		let sql = `
            SELECT
                a.id,
                a.timestamp,
                s.id as student_id,
                s.first_name,
                s.last_name,
                c.name as class_name
            FROM attendance a
            JOIN students s ON a.user_id = s.id
            JOIN classes c ON a.class_id = c.id
        `;
		const params: any = {};
		const conditions: string[] = [];

		if (filters.classId) {
			conditions.push("a.class_id = $classId");
			params["$classId"] = filters.classId;
		}

		if (filters.date) {
			conditions.push("date(a.timestamp) = $date");
			params["$date"] = filters.date;
		}

		if (conditions.length > 0) {
			sql += " WHERE " + conditions.join(" AND ");
		}

		sql += " ORDER BY a.timestamp DESC";

		const query = db.query(sql);
		return query.all(params);
	}
}
