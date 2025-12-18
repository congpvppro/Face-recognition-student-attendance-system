import { fail } from "@sveltejs/kit";
import { api, tsApi } from "$lib/server/http";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const client = api(event);
  const tsClient = tsApi(event);
  const token = event.locals.token;
  let parents = [];
  let classes = [];
  let links = [];

  try {
    const { users } = await client
      .get("api/users/role/parent", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      .json<{ users: any[] }>();
    parents = users;
  } catch (error) {
    console.error("Failed to load parents:", error);
  }

  try {
    // Classes still come from TypeScript API
    classes = await tsClient.get("api/classes").json<any[]>();
  } catch (error) {
    console.error("Failed to load classes:", error);
  }

  try {
    const response = await client
      .get("api/users/parent-student/links", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      .json<{ links: any[] }>();
    links = response.links;
  } catch (error) {
    console.error("Failed to load links:", error);
  }

  return { parents, classes, links };
};

export const actions: Actions = {
  createParent: async (event) => {
    const fd = await event.request.formData();
    const client = api(event);
    const token = event.locals.token;

    const email = String(fd.get("email"));
    const username = String(fd.get("username"));
    const password = String(fd.get("password"));
    const first_name = String(fd.get("first_name"));
    const last_name = String(fd.get("last_name"));

    if (!email || !username || !password || !first_name || !last_name) {
      return fail(400, { message: "All fields are required." });
    }

    try {
      await client
        .post("api/users", {
          json: {
            email,
            username,
            password,
            first_name,
            last_name,
            role: "parent",
          },
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        .json();

      return { success: true, message: "Parent created successfully." };
    } catch (e: any) {
      console.error("An unexpected error occurred:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message:
          body?.detail ?? body?.message ?? "An unexpected error occurred.",
      });
    }
  },
  updateParent: async (event) => {
    const fd = await event.request.formData();
    const id = String(fd.get("id"));
    const email = String(fd.get("email"));
    const username = String(fd.get("username"));
    const first_name = String(fd.get("first_name"));
    const last_name = String(fd.get("last_name"));
    const password = String(fd.get("password"));
    const token = event.locals.token;

    if (!id || !email || !username || !first_name || !last_name) {
      return fail(400, { message: "All fields are required." });
    }

    const payload: any = { email, username, first_name, last_name };
    if (password) {
      payload.password = password;
    }

    const client = api(event);

    try {
      await client
        .put(`api/users/${id}`, {
          json: payload,
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        .json();
    } catch (e: any) {
      console.error("An unexpected error occurred during API call:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message:
          body?.detail ??
          body?.message ??
          "An unexpected error occurred. Please try again.",
      });
    }

    return { success: true, message: "Parent updated successfully." };
  },
  linkStudent: async (event) => {
    const fd = await event.request.formData();
    const parentId = Number(fd.get("parentId"));
    const studentId = String(fd.get("studentId"));
    const client = api(event);
    const token = event.locals.token;

    if (!parentId || !studentId) {
      return fail(400, { message: "Parent ID and Student ID are required." });
    }

    try {
      await client
        .post("api/users/parent-student/link", {
          json: { parent_id: parentId, student_id: studentId },
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        .json();
      return { success: true, message: "Student linked successfully." };
    } catch (e: any) {
      console.error("Failed to link student:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message: body?.detail ?? body?.message ?? "Failed to link student.",
      });
    }
  },
};
