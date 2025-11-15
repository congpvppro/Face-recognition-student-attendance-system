import { fail } from "@sveltejs/kit";
import { api } from "$lib/server/http";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
	const client = api(event);
	try {
		const [students, classes] = await Promise.all([
			client.get("api/students").json(),
			client.get("api/classes").json(),
		]);
		return { students, classes };
	} catch (error) {
		console.error("Failed to load data:", error);
		return { students: [], classes: [] };
	}
};

export const actions: Actions = {
	createStudent: async (event) => {
		const fd = await event.request.formData();
		const id = String(fd.get("id") ?? "");
		const first_name = String(fd.get("first_name") ?? "");
		const last_name = String(fd.get("last_name") ?? "");
		const classId = Number(fd.get("classId"));

		if (!id || !first_name || !last_name || !classId) {
			return fail(400, { message: "All fields are required." });
		}

		const payload = { id, first_name, last_name, class_id: classId };
		const client = api(event);

		try {
			await client.post("api/students", { json: payload }).json();
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

	deleteStudent: async (event) => {
		const fd = await event.request.formData();
		const id = String(fd.get("id"));

		if (!id) {
			return fail(400, { message: "Student ID is required." });
		}

		const client = api(event);

		try {
			await client.delete(`api/students/${id}`);
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

	updateStudent: async (event) => {
		const fd = await event.request.formData();
		const id = String(fd.get("id") ?? "");
		const first_name = String(fd.get("first_name") ?? "");
		const last_name = String(fd.get("last_name") ?? "");
		const classId = Number(fd.get("classId"));

		if (!id || !first_name || !last_name || !classId) {
			return fail(400, { message: "All fields are required." });
		}

		const payload = { first_name, last_name, class_id: classId };
		const client = api(event);

		try {
			await client.patch(`api/students/${id}`, { json: payload }).json();
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
