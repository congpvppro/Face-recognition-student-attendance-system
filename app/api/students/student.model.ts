import { t } from "elysia";

export const StudentSchema = t.Object({
	id: t.String(),
	first_name: t.String(),
	last_name: t.String(),
	class_id: t.Number(),
	class_name: t.Optional(t.String()),
});

export const CreateStudentSchema = StudentSchema;
