import { AttendanceService } from "@attendance/attendance.service";
import { NotFoundError } from "@common/errors/httpErrors";
import { Elysia, t } from "elysia";
import { faceRecognitionGateway } from "../gateway";
import { CreateStudentSchema, StudentSchema } from "./student.model";
import { StudentService } from "./student.service";
import { UnregisteredFaceService } from "./unregistered.service";

export const studentsPlugin = new Elysia({ prefix: "/students" })
	.decorate("studentService", new StudentService())
	.decorate("unregisteredFaceService", new UnregisteredFaceService())
	.decorate("attendanceService", new AttendanceService())
	.get(
		"/",
		({ studentService, set }) => {
			set.headers["Cache-Control"] =
				"public, max-age=300, stale-while-revalidate=300";
			return studentService.getStudents();
		},
		{
			response: t.Array(StudentSchema),
		},
	)
	.get("/unregistered", ({ unregisteredFaceService }) => {
		return unregisteredFaceService.getUnregisteredFaces();
	})
	.get("/unregistered/image/:faceId", async ({ params: { faceId }, set }) => {
		const pythonApiUrl = process.env.PYTHON_API_URL || "http://localhost:8000";
		const response = await fetch(`${pythonApiUrl}/unregistered_face/${faceId}`);

		if (!response.ok) {
			throw new NotFoundError("Image not found.");
		}

		set.headers["Cache-Control"] = "public, max-age=31536000, immutable";
		return response;
	})
	.delete(
		"/unregistered/:faceId",
		({ params: { faceId }, unregisteredFaceService }) => {
			unregisteredFaceService.deleteUnregisteredFace(faceId);
			return { message: "Unregistered face deleted successfully." };
		},
		{
			params: t.Object({ faceId: t.String() }),
		},
	)
	.post(
		"/",
		({ body, studentService }) => {
			return studentService.createStudent(body as any);
		},
		{
			body: CreateStudentSchema,
			response: StudentSchema,
		},
	)
	.post(
		"/:id/face",
		({ params: { id }, body, studentService }) => {
			return studentService.addStudentFace(id, body.image);
		},
		{
			params: t.Object({ id: t.String() }),
			body: t.Object({
				image: t.File(),
			}),
			response: t.Object({
				message: t.String(),
			}),
		},
	)
	.post(
		"/register-face",
		async ({ body, unregisteredFaceService }) => {
			const classId = Number(body.classId);
			const image = body.image as File;

			const recognitionResult = await faceRecognitionGateway.registerFace(
				image,
				classId,
			);
			unregisteredFaceService.addUnregisteredFace(
				recognitionResult.face_id,
				classId,
			);

			return recognitionResult;
		},
		{
			body: t.Object({
				image: t.File(),
				classId: t.String(),
			}),
			response: t.Object({
				face_id: t.String(),
				message: t.String(),
			}),
		},
	)
	.post(
		"/commit-face",
		async ({ body }) => {
			return faceRecognitionGateway.commitFace(body.studentId, body.faceId);
		},
		{
			body: t.Object({
				studentId: t.String(),
				faceId: t.String(),
			}),
			response: t.Object({
				message: t.String(),
			}),
		},
	)
	.delete(
		"/:id",
		async ({ params: { id }, studentService }) => {
			return studentService.deleteStudent(id);
		},
		{
			params: t.Object({ id: t.String() }),
		},
	)
	.patch(
		"/:id",
		({ params: { id }, body, studentService }) => {
			return studentService.updateStudent(id, body as any);
		},
		{
			params: t.Object({ id: t.String() }),
			body: t.Partial(CreateStudentSchema),
			response: StudentSchema,
		},
	);
