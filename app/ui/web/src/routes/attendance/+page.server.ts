import { api } from "$lib/server/http";
import type { PageLoad } from "./$types";

export const load: PageLoad = async (event) => {
	const client = api(event);
	try {
		const classes = await client.get("api/classes").json();
		return { classes };
	} catch (error) {
		console.error("Failed to load classes:", error);
		return { classes: [] };
	}
};
