import { t } from "elysia";

export const RecognitionResponseSchema = t.Object({
	student_id: t.String(),
	similarity: t.Number(),
});

export const AttendanceSchema = t.Object({
	id: t.Number(),
	user_id: t.Number(),
	timestamp: t.String(),
});
