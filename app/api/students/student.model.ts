import { t } from "elysia";

// Student schema matching unified database
export const StudentSchema = t.Object({
  id: t.String(),
  name: t.String(),
  first_name: t.Union([t.String(), t.Null()]),
  last_name: t.Union([t.String(), t.Null()]),
  class_id: t.Union([t.Number(), t.Null()]),
  class_name: t.Optional(t.Union([t.String(), t.Null()])),
  face_registered: t.Optional(t.Union([t.Number(), t.Null()])),
});

// Schema for creating a new student
export const CreateStudentSchema = t.Object({
  id: t.String(),
  first_name: t.String(),
  last_name: t.String(),
  class_id: t.Number(),
});

// Schema for updating a student
export const UpdateStudentSchema = t.Partial(
  t.Object({
    first_name: t.String(),
    last_name: t.String(),
    class_id: t.Number(),
  }),
);
