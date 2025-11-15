import { redirect } from "@sveltejs/kit";

/** @type {import('./$types').PageServerLoad} */
export function load({ locals }) {
	if (!locals.user) {
	}

	return {
		user: locals.user,
	};
}
