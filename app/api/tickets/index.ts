import { Elysia, t } from "elysia";
import { jwt } from "@elysiajs/jwt";
import { UnauthorizedError, ForbiddenError } from "@common/errors/httpErrors";
import { TicketService } from "./ticket.service";
import {
  CreateTicketSchema,
  UpdateTicketStatusSchema,
  TicketSchema,
} from "./ticket.model";

export const ticketsPlugin = new Elysia({ prefix: "/tickets" })
  .use(jwt({ name: "jwt", secret: process.env.JWT_SECRET as string }))
  .decorate("ticketService", new TicketService())
  .guard(
    {
      beforeHandle: async ({ jwt, cookie }) => {
        const token = cookie?.auth?.value;
        if (!token) throw new UnauthorizedError("Missing token");

        const payload = await jwt.verify(token);
        if (!payload) throw new UnauthorizedError("Invalid or expired token");
      },
    },
    (app) =>
      app
        .resolve(async ({ jwt, cookie }) => {
          const token = cookie?.auth?.value as string;
          const user = (await jwt.verify(token)) as {
            id: number;
            role: string;
          } | null;
          return { user };
        })

        // Parent creates a ticket
        .post(
          "/",
          async ({ body, user, ticketService }) => {
            if (user?.role !== "parent") {
              throw new ForbiddenError("Only parents can create tickets.");
            }
            return ticketService.createTicket(body, user.id);
          },
          {
            body: CreateTicketSchema,
            response: { 201: TicketSchema },
          },
        )

        // Get tickets (role-based)
        .get("/", async ({ user, ticketService }) => {
          if (user?.role === "parent") {
            const tickets = await ticketService.getTicketsForParent(user.id);
            return { tickets };
          }
          if (user?.role === "teacher") {
            const tickets = await ticketService.getTicketsForTeacher(user.id);
            return { tickets };
          }
          throw new ForbiddenError(
            "You are not authorized to view these tickets.",
          );
        })

        // Teacher updates a ticket status
        .patch(
          "/:id/status",
          async ({ params, body, user, ticketService }) => {
            if (user?.role !== "teacher") {
              throw new ForbiddenError(
                "Only teachers can update ticket status.",
              );
            }
            return ticketService.updateTicketStatus(
              params.id,
              body.status,
              user.id,
            );
          },
          {
            params: t.Object({ id: t.Numeric() }),
            body: UpdateTicketStatusSchema,
            response: { 200: TicketSchema },
          },
        ),
  );
