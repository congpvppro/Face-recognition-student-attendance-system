import { t } from "elysia";

export const TicketStatusSchema = t.Union([
  t.Literal("pending"),
  t.Literal("approved"),
  t.Literal("rejected"),
]);

export const TicketTypeSchema = t.Union([
  t.Literal("leave"),
  t.Literal("late"),
  t.Literal("other"),
]);

export const TicketSchema = t.Object({
  id: t.Number(),
  parent_id: t.Number(),
  student_id: t.String(),
  teacher_id: t.Number(),
  class_id: t.Number(),
  status: TicketStatusSchema,
  type: TicketTypeSchema,
  reason: t.String(),
  created_at: t.String(),
  updated_at: t.String(),
});

export const CreateTicketSchema = t.Object({
  student_id: t.String(),
  class_id: t.Number(),
  type: TicketTypeSchema,
  reason: t.String({ minLength: 10 }),
});

export const UpdateTicketStatusSchema = t.Object({
  status: t.Union([t.Literal("approved"), t.Literal("rejected")]),
});
