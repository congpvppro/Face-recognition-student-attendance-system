import { AttendanceService } from "@attendance/attendance.service";
import { UnauthorizedError } from "@common/errors/httpErrors";
import { JWT_SECRET, ATTENDANCE_STATUSES } from "@common/config";
import { jwt } from "@elysiajs/jwt";
import { Elysia, t } from "elysia";
import { faceRecognitionGateway } from "../gateway";

// Valid attendance status values matching Python DB schema
const AttendanceStatusEnum = t.Union(
  ATTENDANCE_STATUSES.map((status) => t.Literal(status)) as [
    ReturnType<typeof t.Literal>,
    ...ReturnType<typeof t.Literal>[],
  ],
);

export const attendancePlugin = new Elysia({ prefix: "/attendance" })
  .use(jwt({ name: "jwt", secret: JWT_SECRET }))
  .decorate("attendanceService", new AttendanceService())
  .post(
    "/recognize",
    async ({ body }) => {
      const recognitionResult = await faceRecognitionGateway.recognize(
        body.image,
      );
      const studentId = recognitionResult.student_id;

      // Attendance is marked by the Python agent upon face recognition/tracking
      return {
        ...recognitionResult,
        message: `Recognized student ${studentId}`,
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
            const { classId, date, studentId } = query;

            if (studentId) {
              return attendanceService.getAttendanceByStudent(studentId);
            }

            return attendanceService.getAttendance({
              classId: classId ? Number(classId) : undefined,
              date: date || undefined,
            });
          },
          {
            query: t.Object({
              classId: t.Optional(t.Numeric()),
              date: t.Optional(t.String()),
              studentId: t.Optional(t.String()),
            }),
          },
        )
        .patch(
          "/",
          ({ attendanceService, body, user }) => {
            if (user?.role !== "teacher" && user?.role !== "admin") {
              throw new UnauthorizedError(
                "Only teachers or admins can update attendance.",
              );
            }
            return attendanceService.updateAttendanceStatus(
              body.studentId,
              body.date,
              body.session,
              body.status,
            );
          },
          {
            body: t.Object({
              studentId: t.String(),
              date: t.String(),
              session: t.Numeric(),
              status: AttendanceStatusEnum,
            }),
          },
        ),
  );
