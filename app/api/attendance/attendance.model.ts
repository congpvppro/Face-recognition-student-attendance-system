import { t } from "elysia";

// Face recognition response schema
export const RecognitionResponseSchema = t.Object({
  student_id: t.String(),
  similarity: t.Number(),
});

// Attendance status enum matching Python DB schema
export const AttendanceStatusSchema = t.Union([
  t.Literal("on_time"),
  t.Literal("late"),
  t.Literal("absent"),
  t.Literal("excused"),
  t.Literal("left_early"),
]);

// Attendance session record schema (matches Python DB attendance_sessions table)
export const AttendanceSessionSchema = t.Object({
  id: t.Optional(t.Number()),
  student_id: t.String(),
  session_date: t.String(),
  entry_time: t.Nullable(t.String()),
  exit_time: t.Nullable(t.String()),
  duration_minutes: t.Optional(t.Nullable(t.Number())),
  status: t.Optional(t.Union([t.Literal("present"), t.Literal("left")])),
  attendance_status: AttendanceStatusSchema,
  late_minutes: t.Number(),
  session_number: t.Number(),
  attendance_score: t.Optional(t.Nullable(t.Number())),
});

// Query filters for attendance
export const AttendanceFiltersSchema = t.Object({
  classId: t.Optional(t.Number()),
  date: t.Optional(t.String()),
  studentId: t.Optional(t.String()),
});

// Update attendance request schema
export const UpdateAttendanceSchema = t.Object({
  studentId: t.String(),
  date: t.String(),
  session: t.Number(),
  status: AttendanceStatusSchema,
});
