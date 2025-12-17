import { tsApi } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const client = tsApi(event);
  try {
    const classes = await client.get("api/classes").json();
    return { classes };
  } catch (error) {
    console.error("Failed to load classes:", error);
    return { classes: [] };
  }
};
