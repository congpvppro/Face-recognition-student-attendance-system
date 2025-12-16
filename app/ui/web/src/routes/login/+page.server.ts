import { type Actions, fail, redirect } from "@sveltejs/kit";
import { HTTPError } from "ky";
import { api } from "$lib/server/http";

export const actions: Actions = {
  logout: async (event) => {
    console.log("Logout action triggered");
    event.cookies.delete("auth", {
      path: "/",
      httpOnly: true,
      sameSite: "lax",
    });
    throw redirect(303, "/login");
  },
  login: async (event) => {
    const fd = await event.request.formData();
    const email = String(fd.get("email") ?? "");
    const password = String(fd.get("password") ?? "");

    if (!email || !password) {
      return fail(400, { message: "Email and password are required." });
    }

    const payload = { email, password };
    const client = api(event);

    try {
      const response = await client
        .post("api/auth/login", { json: payload })
        .json<{ token: string }>();

      event.cookies.set("auth", response.token, {
        path: "/",
        httpOnly: true,
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7, // 7 days
      });

      // Fetch user to determine redirect
      const { user } = await client
        .get("api/users/me", {
          headers: {
            Authorization: `Bearer ${response.token}`,
          },
        })
        .json<{ user: { role: string } }>();

      if (user.role === "admin") throw redirect(303, "/admin/statistics");
      if (user.role === "teacher") throw redirect(303, "/teacher/classes");
      if (user.role === "parent") throw redirect(303, "/parent/dashboard");
    } catch (e) {
      // SvelteKit redirects are thrown as errors, so we need to catch and re-throw them
      if (e && typeof e === "object" && "status" in e && "location" in e) {
        throw e;
      }
      if (e instanceof HTTPError) {
        const body = await e.response.json().catch(() => null);
        return fail(e.response.status ?? 400, {
          message: body?.message ?? "Invalid credentials or server error.",
        });
      }
      console.error("An unexpected error occurred during API call:", e);
      return fail(500, {
        message: "An unexpected error occurred. Please try again.",
      });
    }

    return { success: true, message: "Login successful!" };
  },
};
