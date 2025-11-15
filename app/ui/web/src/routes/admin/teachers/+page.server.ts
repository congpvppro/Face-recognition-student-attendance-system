import { fail } from "@sveltejs/kit";
import { api } from "$lib/server/http";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
	const client = api(event);
	try {
		const { users } = await client.get("api/users").json<{ users: any[] }>();
		const teachers = users.filter((user: any) => user.role === "teacher");
		return { teachers };
	} catch (error) {
		console.error("Failed to load teachers:", error);
		return { teachers: [] };
	}
};

export const actions: Actions = {
	createTeacher: async (event) => {
		const fd = await event.request.formData();
		const client = api(event);

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
						role: "teacher",
					},
				})
				.json();

			return { success: true, message: "Teacher created successfully." };
		} catch (e: any) {
			console.error("An unexpected error occurred:", e);
			const body = await e.response?.json().catch(() => null);
			return fail(e.response?.status ?? 500, {
				message: body?.message ?? "An unexpected error occurred.",
			});
		}
	},
	updateTeacher: async (event) => {
		const fd = await event.request.formData();
		const id = String(fd.get("id"));
		const email = String(fd.get("email"));
		const username = String(fd.get("username"));
		const first_name = String(fd.get("first_name"));
		const last_name = String(fd.get("last_name"));

		if (!id || !email || !username || !first_name || !last_name) {
			return fail(400, { message: "All fields are required." });
		}

		const payload = { email, username, first_name, last_name };
		const client = api(event);

		try {
			await client.patch(`api/users/${id}`, { json: payload }).json();
		} catch (e: any) {
			console.error("An unexpected error occurred during API call:", e);
			const body = await e.response?.json().catch(() => null);
			return fail(e.response?.status ?? 500, {
				message:
					body?.message ?? "An unexpected error occurred. Please try again.",
			});
		}

		return { success: true };
	},
};
