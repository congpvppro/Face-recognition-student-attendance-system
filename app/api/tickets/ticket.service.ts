import { db } from "@user/sqlite";
import { NotFoundError, UnauthorizedError } from "@common/errors/httpErrors";
import type { Static } from "elysia";
import type { CreateTicketSchema, TicketSchema } from "./ticket.model";

type Ticket = Static<typeof TicketSchema>;
type CreateTicket = Static<typeof CreateTicketSchema>;

export class TicketService {
  constructor() {
    // Database tables are now initialized in sqlite.ts
  }

  async createTicket(data: CreateTicket, parentId: number): Promise<Ticket> {
    // 1. Verify student is linked to parent
    const linkQuery = db.query(
      "SELECT * FROM parent_student WHERE parent_id = $parentId AND student_id = $studentId",
    );
    const link = linkQuery.get({
      $parentId: parentId,
      $studentId: data.student_id,
    });
    if (!link) {
      throw new UnauthorizedError(
        "You are not authorized to submit a ticket for this student.",
      );
    }

    // 2. Get teacher_id from class
    const classQuery = db.query<{ teacher_id: number }, { $id: number }>(
      "SELECT teacher_id FROM classes WHERE id = $id",
    );
    const course = classQuery.get({ $id: data.class_id });
    if (!course) {
      throw new NotFoundError(`Class with ID ${data.class_id} not found.`);
    }

    const insertQuery = db.query<Ticket, any>(`
            INSERT INTO tickets (parent_id, student_id, teacher_id, class_id, type, reason)
            VALUES ($parent_id, $student_id, $teacher_id, $class_id, $type, $reason)
            RETURNING *
        `);

    const newTicket = insertQuery.get({
      $parent_id: parentId,
      $student_id: data.student_id,
      $teacher_id: course.teacher_id,
      $class_id: data.class_id,
      $type: data.type,
      $reason: data.reason,
    });

    if (!newTicket) {
      throw new Error("Failed to create ticket.");
    }
    return newTicket;
  }

  async getTicketsForParent(parentId: number): Promise<any[]> {
    const query = db.query(`
            SELECT
                t.*,
                s.name as student_name,
                s.first_name as student_first_name,
                s.last_name as student_last_name,
                c.name as class_name,
                u.first_name as teacher_first_name,
                u.last_name as teacher_last_name
            FROM tickets t
            JOIN students s ON t.student_id = s.id
            JOIN classes c ON t.class_id = c.id
            LEFT JOIN users u ON t.teacher_id = u.id
            WHERE t.parent_id = $parentId
            ORDER BY t.created_at DESC
        `);
    return query.all({ $parentId: parentId });
  }

  async getTicketsForTeacher(teacherId: number): Promise<any[]> {
    const query = db.query(`
             SELECT
                t.*,
                s.name as student_name,
                s.first_name as student_first_name,
                s.last_name as student_last_name,
                p.first_name as parent_first_name,
                p.last_name as parent_last_name,
                c.name as class_name
            FROM tickets t
            JOIN students s ON t.student_id = s.id
            JOIN users p ON t.parent_id = p.id
            JOIN classes c ON t.class_id = c.id
            WHERE t.teacher_id = $teacherId
            ORDER BY t.status ASC, t.created_at DESC
        `);
    return query.all({ $teacherId: teacherId });
  }

  async updateTicketStatus(
    ticketId: number,
    status: "approved" | "rejected",
    teacherId: number,
  ): Promise<Ticket> {
    const query = db.query<Ticket, { $id: number; $teacher_id: number }>(
      "SELECT * FROM tickets WHERE id = $id AND teacher_id = $teacher_id",
    );
    const ticket = query.get({ $id: ticketId, $teacher_id: teacherId });

    if (!ticket) {
      throw new NotFoundError(
        "Ticket not found or you are not authorized to update it.",
      );
    }

    const updateQuery = db.query<Ticket, { $id: number; $status: string }>(`
            UPDATE tickets
            SET status = $status, updated_at = CURRENT_TIMESTAMP
            WHERE id = $id
            RETURNING *
        `);

    const updatedTicket = updateQuery.get({ $id: ticketId, $status: status });
    if (!updatedTicket) {
      throw new Error("Failed to update ticket status.");
    }
    return updatedTicket;
  }
}
