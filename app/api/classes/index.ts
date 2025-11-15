import { Elysia, t } from "elysia";
import { ClassSchema, CreateClassSchema } from "./class.model";
import { ClassService } from "./class.service";

const StudentInClassSchema = t.Object({
	id: t.String(),
	first_name: t.String(),
	last_name: t.String(),
});

const ClassWithTeacherSchema = t.Object({
	id: t.Number(),
	name: t.String(),
	teacher: t.Nullable(t.String()),
	students: t.Array(StudentInClassSchema),
});

export const classesPlugin = new Elysia({ prefix: "/classes" })
	.decorate("classService", new ClassService())
	.get(
		"/",
		({ classService, set }) => {
			set.headers["Cache-Control"] =
				"public, max-age=3600, stale-while-revalidate=3600";
			return classService.getClasses();
		},
		{
			response: t.Array(ClassWithTeacherSchema),
		},
	)
	.post("/", ({ body, classService }) => classService.createClass(body), {
		body: CreateClassSchema,
		response: ClassSchema,
	})
	.post(
		"/enroll",
		({ body, classService }) =>
			classService.enrollStudent(body.studentId, body.classId),
		{
			body: t.Object({
				studentId: t.String(),
				classId: t.Number(),
			}),
		},
	);
