import type { RequestEvent } from "@sveltejs/kit";
import ky, { type KyInstance, type Options } from "ky";

// Python FastAPI server for user management and face recognition
const PYTHON_API_URL = "http://localhost:8000/";
// TypeScript Elysia server for other services (attendance, classes, etc.)
const TS_API_URL = "http://localhost:3000/";

export function api(event: RequestEvent, options: Options = {}): KyInstance {
  const defaultOptions: Options = {
    prefixUrl: PYTHON_API_URL,
    credentials: "include",
    fetch: event.fetch,
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

// Legacy API client for TypeScript Elysia server (attendance, classes, students, tickets)
export function tsApi(event: RequestEvent, options: Options = {}): KyInstance {
  // Get the auth token from locals (set by hooks.server.ts)
  const token = event.locals.token;

  const defaultOptions: Options = {
    prefixUrl: TS_API_URL,
    credentials: "include",
    fetch: event.fetch,
    timeout: 10000,
    retry: { limit: 2 },
    hooks: {
      beforeRequest: [
        (request) => {
          // Forward the auth cookie to the TypeScript API
          if (token) {
            request.headers.set("Cookie", `auth=${token}`);
          }
        },
      ],
      afterResponse: [
        async (_request, _options, response) => {
          if (!response.ok) {
            const body = await response.text();
            console.error(
              `TS API request to ${response.url} failed: ${response.status} ${response.statusText}`,
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
