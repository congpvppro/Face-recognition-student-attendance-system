import { redirect } from "@sveltejs/kit";
import { api } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const { locals } = event;
  if (!locals.user) {
    throw redirect(303, "/login");
  }

  let students = [];
  if (locals.user.role === "parent") {
    const client = api(event);
    try {
      const response = await client
        .get("api/users/me/students")
        .json<{ students: any[] }>();
      students = response.students;
    } catch (e) {
      console.error("Failed to load students for parent:", e);
    }
  }

  return {
    user: locals.user,
    students,
  };
};
