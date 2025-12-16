import { fail } from "@sveltejs/kit";
import { api } from "$lib/server/http";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const client = api(event);
  const { user } = event.locals;

  try {
    // All API calls are now made in parallel
    const [unregisteredFacesRes, studentsRes, classesRes] = await Promise.all([
      client
        .get("api/students/unregistered")
        .json<{ face_id: string; class_id: number }[]>(),
      client.get("api/students").json<any[]>(),
      client.get("api/classes").json<any[]>(),
    ]);

    let classes = classesRes;

    // If the user is a teacher, filter the classes they teach
    if (user?.role === "teacher") {
      classes = classesRes.filter((c) => c.teacher_id === user.id);
    }

    // Get all student IDs from the teacher's classes
    const teacherStudentIds = new Set(
      classes.flatMap((c) => c.students.map((s: any) => s.id)),
    );

    return {
      unregisteredFaces: unregisteredFacesRes,
      students: studentsRes.filter(
        (s) => user?.role !== "teacher" || teacherStudentIds.has(s.id),
      ),
      classes: classes,
    };
  } catch (error) {
    console.error("Failed to load data:", error);
    return { unregisteredFaces: [], students: [], classes: [] };
  }
};

export const actions: Actions = {
  assignStudent: async (event) => {
    const fd = await event.request.formData();
    const client = api(event);
    const faceId = String(fd.get("faceId"));
    const studentId = String(fd.get("studentId"));

    if (!faceId || !studentId) {
      return fail(400, { message: "Face ID and Student ID are required." });
    }

    try {
      // Commit the face to the recognition database via the backend.
      await client
        .post("api/students/commit-face", {
          json: {
            studentId: studentId,
            faceId: faceId,
          },
        })
        .json();

      // Delete the unregistered face record.
      await client.delete(`api/students/unregistered/${faceId}`);

      return {
        success: true,
        message: "Face assigned to student successfully.",
      };
    } catch (e: any) {
      console.error("An unexpected error occurred:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message: body?.message ?? "An unexpected error occurred.",
      });
    }
  },
  createAndAssignStudent: async (event) => {
    const fd = await event.request.formData();
    const client = api(event);
    const faceId = String(fd.get("faceId"));
    const classId = Number(fd.get("classId"));
    const studentId = String(fd.get("studentId"));
    const firstName = String(fd.get("firstName"));
    const lastName = String(fd.get("lastName"));

    if (!faceId || !classId || !studentId || !firstName || !lastName) {
      return fail(400, { message: "All fields are required." });
    }

    try {
      // Create the new student
      await client
        .post("api/students", {
          json: {
            id: studentId,
            first_name: firstName,
            last_name: lastName,
            class_id: classId,
          },
        })
        .json();

      // Assign the face to the new student
      await client
        .post("api/students/commit-face", {
          json: {
            studentId: studentId,
            faceId: faceId,
          },
        })
        .json();

      // Delete the unregistered face record
      await client.delete(`api/students/unregistered/${faceId}`);

      return {
        success: true,
        message: "Student created and assigned successfully.",
      };
    } catch (e: any) {
      console.error("An unexpected error occurred:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message: body?.message ?? "An unexpected error occurred.",
      });
    }
  },
  ignoreFace: async (event) => {
    const fd = await event.request.formData();
    const client = api(event);
    const faceId = String(fd.get("faceId"));

    if (!faceId) {
      return fail(400, { message: "Face ID is required." });
    }

    try {
      // Delete the unregistered face record.
      await client.delete(`api/students/unregistered/${faceId}`);

      return { success: true, message: "Face ignored successfully." };
    } catch (e: any) {
      console.error("An unexpected error occurred:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message: body?.message ?? "An unexpected error occurred.",
      });
    }
  },
};
