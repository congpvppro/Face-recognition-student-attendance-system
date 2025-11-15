import {
	ConflictError,
	InternalServerError,
	NotFoundError,
} from "@common/errors/httpErrors";
import { db } from "@user/sqlite";
import type { Static } from "elysia";
import ky from "ky";
import type { CreateStudentSchema, StudentSchema } from "./student.model";
import { UnregisteredFaceService } from "./unregistered.service";

type Student = Static<typeof StudentSchema>;
type CreateStudent = Static<typeof CreateStudentSchema>;

export class StudentService {
	private unregisteredFaceService: UnregisteredFaceService;

	constructor() {
		this.initDatabase();
		this.unregisteredFaceService = new UnregisteredFaceService();
	}

	private initDatabase() {
		db.run(`
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                class_id INTEGER NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes (id)
            );
        `);
	}

	public createStudent(studentData: CreateStudent): Student {
		const existingStudent = db
			.query("SELECT id FROM students WHERE id = $id")
			.get({ $id: studentData.id });
		if (existingStudent) {
			throw new ConflictError(
				`Student with ID ${studentData.id} already exists.`,
			);
		}

		const query = db.query<
			Student,
			{
				$id: string;
				$first_name: string;
				$last_name: string;
				$class_id: number;
			}
		>(
			"INSERT INTO students (id, first_name, last_name, class_id) VALUES ($id, $first_name, $last_name, $class_id) RETURNING *",
		);

		const newStudent = query.get({
			$id: studentData.id,
			$first_name: studentData.first_name,
			$last_name: studentData.last_name,
			$class_id: studentData.class_id,
		});

		if (!newStudent) {
			throw new InternalServerError("Failed to create student.");
		}

		return newStudent;
	}

	public getStudentById(id: string): Student {
		const query = db.query<Student, { $id: string }>(
			"SELECT * FROM students WHERE id = $id",
		);
		const student = query.get({ $id: id });
		if (!student) {
			throw new NotFoundError(`Student with ID ${id} not found.`);
		}
		return student;
	}

	public getStudents(): any[] {
		const query = db.query(`
            SELECT
                s.id,
                s.first_name,
                s.last_name,
                s.class_id,
                c.name as class_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
        `);
		return query.all();
	}
	public updateStudent(
		id: string,
		studentData: Partial<CreateStudent>,
	): Student {
		const student = this.getStudentById(id);

		const updatedStudent = {
			...student,
			...studentData,
		};

		const query = db.query<
			Student,
			{
				$id: string;
				$first_name: string;
				$last_name: string;
				$class_id: number;
			}
		>(
			"UPDATE students SET first_name = $first_name, last_name = $last_name, class_id = $class_id WHERE id = $id RETURNING *",
		);

		const result = query.get({
			$id: id,
			$first_name: updatedStudent.first_name,
			$last_name: updatedStudent.last_name,
			$class_id: updatedStudent.class_id,
		});

		if (!result) {
			throw new InternalServerError("Failed to update student.");
		}

		return result;
	}

	public async deleteStudent(id: string): Promise<{ message: string }> {
		const query = db.query("DELETE FROM students WHERE id = $id RETURNING id");
		const deletedStudent = query.get({ $id: id });

		if (!deletedStudent) {
			throw new NotFoundError(`Student with ID ${id} not found.`);
		}

		try {
			const pythonApiUrl =
				process.env.PYTHON_API_URL || "http://localhost:8000";
			await ky.delete(`${pythonApiUrl}/delete_face/${id}`);
		} catch (error: any) {
			console.error(`Failed to delete face for student ${id}:`, error);
		}

		return { message: `Student with ID ${id} successfully deleted.` };
	}

	public async addStudentFace(
		studentId: string,
		image: File,
	): Promise<{ message: string }> {
		// check if the student exists in database
		this.getStudentById(studentId); // throw NotFoundError if student doesn't exist

		const formData = new FormData();
		formData.append("student_id", studentId);
		formData.append("file", image);

		try {
			const response: { message: string } = await ky
				.post("http://localhost:8000/add_face", {
					body: formData,
				})
				.json();
			return response;
		} catch (error: any) {
			console.error("Error calling face addition service:", error);
			const errorMessage = await error.response?.json();
			throw new InternalServerError(
				`Face addition service failed: ${errorMessage?.detail || error.message}`,
			);
		}
	}

	public async registerStudentFace(
		classId: number,
		image: File,
	): Promise<{ face_id: string; message: string }> {
		const formData = new FormData();
		formData.append("file", image);

		try {
			const response: { face_id: string; message: string } = await ky
				.post("http://localhost:8000/register_face", {
					body: formData,
				})
				.json();

			// Store the unregistered face in the database
			this.unregisteredFaceService.addUnregisteredFace(
				response.face_id,
				classId,
			);

			return response;
		} catch (error: any) {
			console.error("Error calling face registration service:", error);
			const errorMessage = await error.response?.json();
			throw new InternalServerError(
				`Face registration service failed: ${errorMessage?.detail || error.message}`,
			);
		}
	}

	public async commitStudentFace(
		studentId: string,
		faceId: string,
	): Promise<{ message: string }> {
		const formData = new FormData();
		formData.append("student_id", studentId);
		formData.append("face_id", faceId);

		try {
			const response: { message: string } = await ky
				.post("http://localhost:8000/commit_face", {
					body: formData,
				})
				.json();

			return response;
		} catch (error: any) {
			console.error("Error calling face commit service:", error);
			const errorMessage = await error.response?.json();
			throw new InternalServerError(
				`Face commit service failed: ${errorMessage?.detail || error.message}`,
			);
		}
	}
}
