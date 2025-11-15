import { type Actions, fail } from "@sveltejs/kit";
import { HTTPError } from "ky";
import { api } from "$lib/server/http";

export const actions: Actions = {
	default: async (event) => {
		const fd = await event.request.formData();
		const payload = {
			first_name: String(fd.get("firstName") ?? ""),
			last_name: String(fd.get("lastName") ?? ""),
			username: String(fd.get("username") ?? ""),
			email: String(fd.get("email") ?? ""),
			password: String(fd.get("password") ?? ""),
			confirmPassword: String(fd.get("confirmPassword") ?? ""),
		};

		if (!payload.email || !payload.password) {
			return fail(400, { message: "Email and password are required." });
		}
		if (payload.password !== payload.confirmPassword) {
			return fail(400, { message: "Passwords do not match." });
		}

		const client = api(event);
		try {
			await client.post("api/users", { json: payload }).json();
			return { success: true, message: "Account created successfully!" };
		} catch (e) {
			if (e instanceof HTTPError) {
				const body = await e.response.json().catch(() => null);
				return fail(e.response.status ?? 400, {
					message: body?.message ?? "Sign up failed.",
				});
			}
			return fail(500, { message: "An error occurred. Please try again." });
		}
	},
};
