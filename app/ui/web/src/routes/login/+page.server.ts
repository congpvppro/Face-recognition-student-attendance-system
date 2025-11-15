import { type Actions, fail } from "@sveltejs/kit";
import { HTTPError } from "ky";
import { api } from "$lib/server/http";

export const actions: Actions = {
	default: async (event) => {
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
		} catch (e) {
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
