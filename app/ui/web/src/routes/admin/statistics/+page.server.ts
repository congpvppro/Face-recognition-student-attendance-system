import { api } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const client = api(event);
  const { url } = event;

  // Get classId and date from URL search params, providing defaults
  const classId = url.searchParams.get("classId");
  const date =
    url.searchParams.get("date") || new Date().toISOString().split("T")[0];

  try {
    // Always fetch the list of all classes for the dropdown
    const classes = await client.get("api/classes").json<any[]>();

    let attendance = [];
    let students = [];

    // If a class is selected, fetch its students and attendance for the selected date
    if (classId) {
      const classDetail = classes.find((c) => c.id === Number(classId));
      if (classDetail) {
        students = classDetail.students || [];
      }

      attendance = await client
        .get(`api/attendance?classId=${classId}&date=${date}`)
        .json<any[]>();
    }

    return {
      classes,
      students,
      attendance,
      selectedClassId: classId ? Number(classId) : null,
      selectedDate: date,
    };
  } catch (error) {
    console.error("Failed to load admin attendance data:", error);
    return {
      classes: [],
      students: [],
      attendance: [],
      selectedClassId: null,
      selectedDate: date,
    };
  }
};
