import { tsApi } from "$lib/server/http";
import type { PageServerLoad, Actions } from "./$types";
import { fail } from "@sveltejs/kit";

export const load: PageServerLoad = async (event) => {
  const { classId } = event.params;
  const client = tsApi(event);

  // Fetch class details (which includes students)
  const classes = await client.get("api/classes").json<any[]>();
  const classDetail = classes.find((c) => c.id === Number(classId));

  if (!classDetail) {
    throw fail(404, { message: "Class not found" });
  }

  // Fetch attendance analytics
  const today = new Date().toISOString().split("T")[0];
  let attendance = [];
  try {
    attendance = await client
      .get(`api/attendance?classId=${classId}&date=${today}`)
      .json<any[]>();
  } catch (e) {
    console.error("Failed to fetch attendance:", e);
  }

  return {
    classDetail,
    attendance,
  };
};

export const actions: Actions = {
  addStudent: async (event) => {
    const client = tsApi(event);
    const formData = await event.request.formData();
    const studentId = formData.get("studentId") as string;
    const classId = Number(event.params.classId);

    if (!studentId) {
      return fail(400, { missing: true });
    }

    try {
      await client.post("api/classes/enroll", {
        json: {
          studentId,
          classId,
        },
      });
      return { success: true };
    } catch (err) {
      console.error(err);
      return fail(500, { message: "Failed to enroll student" });
    }
  },
  updateAttendance: async (event) => {
    const client = tsApi(event);
    const formData = await event.request.formData();
    const studentId = formData.get("studentId") as string;
    const status = formData.get("status") as string;
    const date = formData.get("date") as string;
    const session = Number(formData.get("session"));

    if (!studentId || !status || !date || isNaN(session)) {
      return fail(400, { missing: true });
    }

    try {
      await client.patch("api/attendance", {
        json: {
          studentId,
          date,
          session,
          status,
        },
      });
      return { success: true };
    } catch (err) {
      console.error(err);
      return fail(500, { message: "Failed to update attendance" });
    }
  },
};
