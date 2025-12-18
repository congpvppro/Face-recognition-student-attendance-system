import type { Handle } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit"; // Import redirect
import { HTTPError } from "ky";
import { api } from "$lib/server/http";

export const handle: Handle = async ({ event, resolve }) => {
  const requestId = crypto.randomUUID().split("-")[0];

  // 1. AUTHENTICATION: Check for token and load user
  const token = event.cookies.get("auth");

  // Store token in locals for use in server-side API calls
  event.locals.token = token ?? null;

  if (token) {
    const client = api(event);
    try {
      // Pass the token as Bearer authorization to Python API
      const responseData: unknown = await client
        .get("api/users/me", {
          headers: { Authorization: `Bearer ${token}` },
        })
        .json();

      if (
        responseData &&
        typeof responseData === "object" &&
        "user" in responseData &&
        responseData.user
      ) {
        // Assign user to locals
        event.locals.user = responseData.user as App.User;
      } else {
        throw new Error(
          'Invalid data structure: API response is missing the "user" property.',
        );
      }
    } catch (e) {
      if (e instanceof HTTPError) {
        event.cookies.delete("auth", { path: "/" });
      } else {
        console.error("Unexpected error during user authentication:", e);
      }
      event.locals.user = null;
    }
  } else {
    event.locals.user = null;
  }

  // 2. AUTHORIZATION & ROUTE GUARDING
  const user = event.locals.user;
  const url = event.url;
  const path = url.pathname;

  // A. Redirect logged-in users away from auth pages (Login/Register)
  // Exception: Allow logout action to proceed. The action is usually POST /login?/logout
  if (user && (path === "/login" || path === "/register")) {
    const isLogout = path === "/login" && event.url.search.includes("/logout");
    if (!isLogout) {
      if (user.role === "admin") throw redirect(303, "/admin/statistics");
      if (user.role === "teacher") throw redirect(303, "/teacher/classes");
      if (user.role === "parent") throw redirect(303, "/parent/dashboard");
    }
  }

  // B. Define protected route prefixes
  const isAdminRoute = path.startsWith("/admin");
  const isTeacherRoute = path.startsWith("/teacher");
  const isParentRoute = path.startsWith("/parent");
  const isProfileRoute = path.startsWith("/profile");

  // Note: /attendance is public (Kiosk mode) and not included here.

  const isProtectedRoute =
    isAdminRoute || isTeacherRoute || isParentRoute || isProfileRoute;

  // C. Unauthenticated User Guard
  if (isProtectedRoute && !user) {
    // Redirect to login, remembering where they wanted to go
    throw redirect(303, `/login?redirectTo=${path}`);
  }

  // D. Role-Based Access Control (RBAC)
  if (user) {
    if (isAdminRoute && user.role !== "admin") {
      throw redirect(303, "/403"); // Access Denied
    }

    if (isTeacherRoute && user.role !== "teacher") {
      // Optional: Allow admin to view teacher routes?
      // If strict:
      throw redirect(303, "/403");
    }

    if (isParentRoute && user.role !== "parent") {
      throw redirect(303, "/403");
    }
  }

  // 3. RESOLVE REQUEST
  return resolve(event);
};
