import { t } from "elysia";

export const ClassSchema = t.Object({
	id: t.Number(),
	name: t.String(),
	teacher_id: t.Number(),
});

export const CreateClassSchema = t.Omit(ClassSchema, ["id"]);
