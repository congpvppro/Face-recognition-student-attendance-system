import { fail } from "@sveltejs/kit";
import { api, tsApi } from "$lib/server/http";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const userClient = api(event);
  const tsClient = tsApi(event);
  const token = event.locals.token;

  try {
    const [classes, usersResponse] = await Promise.all([
      tsClient.get("api/classes").json<any[]>(),
      userClient
        .get("api/users/role/teacher", {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        .json<{ users: any[] }>(),
    ]);
    return { classes, teachers: usersResponse.users };
  } catch (error) {
    console.error("Failed to load data:", error);
    return { classes: [], teachers: [], students: [] };
  }
};

export const actions: Actions = {
  createClass: async (event) => {
    const fd = await event.request.formData();
    const client = tsApi(event);
    const name = String(fd.get("name"));
    const teacher_id = Number(fd.get("teacher_id"));

    if (!name || !teacher_id) {
      return fail(400, { message: "Class name and teacher are required." });
    }

    try {
      await client
        .post("api/classes", {
          json: {
            name,
            teacher_id,
          },
        })
        .json();

      return { success: true, message: "Class created successfully." };
    } catch (e: any) {
      console.error("An unexpected error occurred:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message: body?.message ?? "An unexpected error occurred.",
      });
    }
  },
};
