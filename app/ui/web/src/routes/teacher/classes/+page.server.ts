import { api } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const client = api(event);

  // Fetch classes. The backend endpoint GET /classes returns all classes.
  // We might need to filter by teacher on the backend or frontend.
  // Ideally backend should support ?teacher_id=... or /teachers/me/classes.
  // But for now, let's fetch all and filter or assume the backend handles it if we send user context.
  // Looking at ClassService.getClasses(), it returns ALL classes.
  // And it doesn't seem to filter by logged in user.

  // Let's modify the backend later to filter. For now, we fetch all.
  const classes = await client.get("api/classes").json<any[]>();

  // Filter for the current teacher
  const teacherId = event.locals.user?.id;
  const myClasses = classes.filter((c) => c.teacher_id === teacherId);

  return {
    classes: myClasses,
  };
};
