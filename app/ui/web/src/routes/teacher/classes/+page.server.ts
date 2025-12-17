import { tsApi } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const client = tsApi(event);

  // Fetch classes. The backend endpoint GET /classes returns all classes.
  const classes = await client.get("api/classes").json<any[]>();

  // Filter for the current teacher
  const teacherId = event.locals.user?.id;
  const myClasses = classes.filter((c) => c.teacher_id === teacherId);

  return {
    classes: myClasses,
  };
};
