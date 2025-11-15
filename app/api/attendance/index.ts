import { AttendanceService } from "@attendance/attendance.service";
import { UnauthorizedError } from "@common/errors/httpErrors";
import { jwt } from "@elysiajs/jwt";
import { Elysia, t } from "elysia";
import { faceRecognitionGateway } from "../gateway";

if (!process.env.JWT_SECRET) {
	console.error("FATAL ERROR: JWT_SECRET is not defined in .env");
	process.exit(1);
}

export const attendancePlugin = new Elysia({ prefix: "/attendance" })
	.use(jwt({ name: "jwt", secret: process.env.JWT_SECRET as string }))
	.decorate("attendanceService", new AttendanceService())
	.post(
		"/recognize",
		async ({ body, attendanceService }) => {
			const classId = Number(body.classId);
			const recognitionResult = await faceRecognitionGateway.recognize(
				body.image,
			);
			const studentId = recognitionResult.student_id;
			await attendanceService.markAttendance(studentId, classId);
			return {
				...recognitionResult,
				message: `Attendance marked for student ${studentId}`,
			};
		},
		{
			body: t.Object({
				image: t.File(),
				classId: t.String(),
			}),
			response: t.Object({
				student_id: t.String(),
				similarity: t.Number(),
				message: t.String(),
			}),
		},
	)
	.guard(
		{
			beforeHandle: async ({ jwt, cookie }) => {
				const token = cookie?.auth?.value;
				if (!token || !(await jwt.verify(token))) {
					throw new UnauthorizedError("Unauthorized");
				}
			},
		},
		(app) =>
			app
				.resolve(async ({ jwt, cookie }) => {
					const token = cookie?.auth?.value;
					const user = token ? await jwt.verify(token) : null;
					return { user };
				})
				.get(
					"/",
					({ attendanceService, query }) => {
						const { classId, date } = query;
						const filters = {
							classId: classId ? Number(classId) : undefined,
							date: date ? String(date) : undefined,
						};
						return attendanceService.getAttendance(filters);
					},
					{
						query: t.Object({
							classId: t.Optional(t.Numeric()),
							date: t.Optional(t.String()),
						}),
					},
				),
	);
