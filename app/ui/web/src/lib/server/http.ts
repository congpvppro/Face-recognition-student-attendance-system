import type { RequestEvent } from "@sveltejs/kit";
import ky, { type KyInstance, type Options } from "ky";

export function api(event: RequestEvent, options: Options = {}): KyInstance {
	const defaultOptions: Options = {
		prefixUrl: "http://localhost:3000/",
		credentials: "include",
		fetch: event.fetch,
		headers: {
			// Forward the cookie from the browser to the API server.
			cookie: event.request.headers.get("cookie") ?? "",
		},
		timeout: 10000,
		retry: { limit: 2 },
		hooks: {
			afterResponse: [
				async (_request, _options, response) => {
					if (!response.ok) {
						const body = await response.text();
						console.error(
							`API request to ${response.url} failed: ${response.status} ${response.statusText}`,
							body,
						);
					}
				},
			],
		},
	};

	const finalOptions = {
		...defaultOptions,
		...options,
		headers: {
			...defaultOptions.headers,
			...options.headers,
		},
	};

	return ky.create(finalOptions);
}
