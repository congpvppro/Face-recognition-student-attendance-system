import { redirect } from "@sveltejs/kit";
import { api } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const { locals } = event;
  if (!locals.user) {
    throw redirect(303, "/login");
  }

  let students = [];
  if (locals.user.role === "parent" && locals.token) {
    const client = api(event);
    try {
      const response = await client
        .get(`api/users/${locals.user.id}/students`, {
          headers: { Authorization: `Bearer ${locals.token}` },
        })
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
