import { api } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const client = api(event);

  try {
    // 1. Get linked students
    const response = await client
      .get("api/users/me/students")
      .json<{ students: any[] }>();
    const students = response.students || [];

    // 2. For each student, get attendance
    const studentsWithAttendance = await Promise.all(
      students.map(async (student) => {
        try {
          const attendance = await client
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
