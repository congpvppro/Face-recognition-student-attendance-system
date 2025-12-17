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
  // Low security mode - authentication handled at SvelteKit level
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
    ({ attendanceService, body }) => {
      // Authentication is handled at SvelteKit level (hooks.server.ts)
      // Only teacher/admin routes can access this endpoint
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
  )
  .get(
    "/export-report",
    ({ attendanceService, query, set }) => {
      // Authentication is handled at SvelteKit level (hooks.server.ts)
      const result = attendanceService.exportStudentReport(
        query.classId,
        query.date || undefined,
      );

      // Set response headers for CSV download
      set.headers["Content-Type"] = "text/csv; charset=utf-8";
      set.headers["Content-Disposition"] =
        `attachment; filename="${result.filename}"`;

      // Add BOM for Excel UTF-8 compatibility
      return "\ufeff" + result.content;
    },
    {
      query: t.Object({
        classId: t.Numeric(),
        date: t.Optional(t.String()),
      }),
    },
  );
