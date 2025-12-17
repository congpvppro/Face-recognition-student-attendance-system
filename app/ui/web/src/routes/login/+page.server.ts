import { type Actions, fail, redirect } from "@sveltejs/kit";
import { HTTPError } from "ky";
import { api } from "$lib/server/http";

export const actions: Actions = {
  logout: async (event) => {
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
      return fail(400, { message: "Email và mật khẩu là bắt buộc." });
    }

    const client = api(event);
    let redirectUrl = "/";

    try {
      const response = await client
        .post("api/auth/login", { json: { email, password } })
        .json<{ token: string }>();

      event.cookies.set("auth", response.token, {
        path: "/",
        httpOnly: true,
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7,
      });

      const { user } = await client
        .get("api/users/me", {
          headers: { Authorization: `Bearer ${response.token}` },
        })
        .json<{ user: { role: string } }>();

      if (user.role === "admin") redirectUrl = "/admin/statistics";
      else if (user.role === "teacher") redirectUrl = "/teacher/classes";
      else if (user.role === "parent") redirectUrl = "/parent/dashboard";
    } catch (e) {
      if (e instanceof HTTPError) {
        const body = await e.response.json().catch(() => null);
        return fail(e.response.status ?? 400, {
          message:
            body?.message ??
            "Thông tin đăng nhập không hợp lệ hoặc lỗi máy chủ.",
        });
      }
      return fail(500, {
        message: "Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.",
      });
    }

    throw redirect(303, redirectUrl);
  },
};
