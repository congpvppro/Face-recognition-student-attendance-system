import { fail } from "@sveltejs/kit";
import { tsApi } from "$lib/server/http";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const client = tsApi(event);
  try {
    const { tickets } = await client
      .get("api/tickets")
      .json<{ tickets: any[] }>();
    return { tickets };
  } catch (error) {
    console.error("Failed to load tickets for teacher:", error);
    return { tickets: [] };
  }
};

export const actions: Actions = {
  updateStatus: async (event) => {
    const fd = await event.request.formData();
    const client = tsApi(event);

    const ticketId = Number(fd.get("ticketId"));
    const status = String(fd.get("status"));

    if (
      !ticketId ||
      !status ||
      (status !== "approved" && status !== "rejected")
    ) {
      return fail(400, { message: "Invalid data provided." });
    }

    try {
      await client
        .patch(`api/tickets/${ticketId}/status`, {
          json: { status },
        })
        .json();
      return {
        success: true,
        message: `Đơn đã được ${status === "approved" ? "duyệt" : "từ chối"}.`,
      };
    } catch (e: any) {
      console.error("Failed to update ticket status:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message: body?.message ?? "Có lỗi xảy ra, vui lòng thử lại.",
      });
    }
  },
};
