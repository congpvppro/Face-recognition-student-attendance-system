import { attendancePlugin } from "@attendance/index";
import { errorHandler } from "@common/errors/errorHandler";
import { cors } from "@elysiajs/cors";
import { openapi } from "@elysiajs/openapi";
import { usersPlugin } from "@user/index";
import { Elysia } from "elysia";
import { classesPlugin } from "./classes";
import { studentsPlugin } from "./students";

export const app = new Elysia({ prefix: "/api" })
	.use(errorHandler)
	.use(
		cors({
			origin: "http://localhost:5173",
			credentials: true,
			methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
			allowedHeaders: ["Content-Type", "Authorization"],
		}),
	)
	.use(
		openapi({
			documentation: {
				info: {
					title: "Attendance API Documentation",
					version: "1.0.0",
				},
			},
		}),
	)

	.use(usersPlugin)
	.use(attendancePlugin)
	.use(studentsPlugin)
	.use(classesPlugin)

	.get("/", () => ({ status: "ok" }), {
		detail: { summary: "Health check endpoint" },
	})

	.listen(3000);

console.log(
	`🦊 Elysia server is running at http://${app.server?.hostname}:${app.server?.port}`,
);

export type App = typeof app;
