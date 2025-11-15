import { InternalServerError, NotFoundError } from "@common/errors/httpErrors";
import { db } from "@user/sqlite";
import type { Static } from "elysia";
import type { ClassSchema, CreateClassSchema } from "./class.model";

type Class = Static<typeof ClassSchema>;
type CreateClass = Static<typeof CreateClassSchema>;

export class ClassService {
	constructor() {
		this.initDatabase();
	}

	private initDatabase() {
		db.run(`
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                teacher_id INTEGER,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            );
        `);
		db.run(`
            CREATE TABLE IF NOT EXISTS student_classes (
                student_id TEXT NOT NULL,
                class_id INTEGER NOT NULL,
                PRIMARY KEY (student_id, class_id),
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (class_id) REFERENCES classes (id)
            );
        `);
	}

	public createClass(classData: CreateClass): Class {
		const query = db.query<Class, { $name: string; $teacher_id: number }>(
			"INSERT INTO classes (name, teacher_id) VALUES ($name, $teacher_id) RETURNING *",
		);
		const newClass = query.get({
			$name: classData.name,
			$teacher_id: classData.teacher_id,
		});
		if (!newClass) {
			throw new InternalServerError(
				"Failed to create class due to a database error.",
			);
		}
		return newClass;
	}

	public getClasses(): any[] {
		const query = db.query(`
            SELECT
                c.id,
                c.name,
                u.first_name || ' ' || u.last_name as teacher,
                (
                    SELECT json_group_array(
                        json_object('id', s.id, 'first_name', s.first_name, 'last_name', s.last_name)
                    )
                    FROM students s
                    WHERE s.class_id = c.id
                ) as students
            FROM classes c
            LEFT JOIN users u ON c.teacher_id = u.id
        `);
		const classes = query.all() as { students: string | null }[];

		return classes.map((cls) => ({
			...cls,
			students: cls.students ? JSON.parse(cls.students) : [],
		}));
	}

	public enrollStudent(
		studentId: string,
		classId: number,
	): { message: string } {
		const studentQuery = db.query("SELECT id FROM students WHERE id = $id");
		const student = studentQuery.get({ $id: studentId });
		if (!student) {
			throw new NotFoundError(`Student with ID ${studentId} not found.`);
		}

		const classQuery = db.query("SELECT id FROM classes WHERE id = $id");
		const course = classQuery.get({ $id: classId });
		if (!course) {
			throw new NotFoundError(`Class with ID ${classId} not found.`);
		}

		const query = db.query(
			"INSERT INTO student_classes (student_id, class_id) VALUES ($studentId, $classId)",
		);
		query.run({ $studentId: studentId, $classId: classId });

		return { message: `Student ${studentId} enrolled in class ${classId}.` };
	}
}
