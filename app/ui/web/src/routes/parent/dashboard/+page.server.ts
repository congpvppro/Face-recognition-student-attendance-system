import { api, tsApi } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const userClient = api(event);
  const tsClient = tsApi(event);
  const token = event.locals.token;
  const userId = event.locals.user?.id;

  try {
    // 1. Get linked students from Python API
    const response = await userClient
      .get(`api/users/${userId}/students`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      .json<{ students: any[] }>();
    const students = response.students || [];

    // 2. For each student, get attendance from TS API
    const studentsWithAttendance = await Promise.all(
      students.map(async (student) => {
        try {
          const attendance = await tsClient
            .get(`api/attendance?studentId=${student.id}`)
            .json<any[]>();
          return { ...student, attendance };
        } catch (e) {
          console.error(
            `Failed to fetch attendance for student ${student.id}`,
            e,
          );
          return { ...student, attendance: [] };
        }
      }),
    );

    return {
      students: studentsWithAttendance,
    };
  } catch (err) {
    console.error("Failed to load parent dashboard data:", err);
    return { students: [] };
  }
};
