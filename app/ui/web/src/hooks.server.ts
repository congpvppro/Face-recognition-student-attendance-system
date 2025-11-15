import type { Handle } from "@sveltejs/kit";
import { HTTPError } from "ky";
import { api } from "$lib/server/http";

export const handle: Handle = async ({ event, resolve }) => {
	const requestId = crypto.randomUUID().split("-")[0];

	const token = event.cookies.get("auth");
	if (!token) {
		event.locals.user = null;
		return resolve(event);
	}

	// API CALL
	const client = api(event);
	try {
		const responseData: unknown = await client.get("api/users/me").json();

		if (
			responseData &&
			typeof responseData === "object" &&
			"user" in responseData &&
			responseData.user
		) {
			event.locals.user = responseData.user as App.User;
		} else {
			throw new Error(
				'Invalid data structure: API response is missing the "user" property.',
			);
		}
	} catch (e) {
		if (e instanceof HTTPError) {
			event.cookies.delete("auth", { path: "/" });
		} else console.error("Unexpected error during user authentication:", e);

		event.locals.user = null;
	}

	return resolve(event);
};
