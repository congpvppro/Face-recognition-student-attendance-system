import { fail } from "@sveltejs/kit";
import { api, tsApi } from "$lib/server/http";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
  const userClient = api(event);
  const tsClient = tsApi(event);
  const token = event.locals.token;
  const userId = event.locals.user?.id;

  let students = [];
  let tickets = [];

  try {
    const studentRes = await userClient
      .get(`api/users/${userId}/students`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      .json<{ students: any[] }>();
    students = studentRes.students;
  } catch (e) {
    console.error("Failed to load students for parent:", e);
  }

  try {
    const ticketRes = await tsClient
      .get("api/tickets")
      .json<{ tickets: any[] }>();
    tickets = ticketRes.tickets;
  } catch (e) {
    console.error("Failed to load tickets for parent:", e);
  }

  // Join class name into students
  try {
    const classes = await tsClient.get("api/classes").json<any[]>();
    students = students.map((s) => {
      const studentClass = classes.find((c) => c.id === s.class_id);
      return { ...s, class_name: studentClass?.name || "N/A" };
    });
  } catch (e) {
    console.error("Failed to load classes:", e);
  }

  return { students, tickets };
};

export const actions: Actions = {
  createTicket: async (event) => {
    const fd = await event.request.formData();
    const client = tsApi(event);

    const student_id = String(fd.get("student_id"));
    const class_id = Number(fd.get("class_id"));
    const type = String(fd.get("type"));
    const reason = String(fd.get("reason"));

    if (!student_id || !class_id || !type || !reason) {
      return fail(400, { message: "Vui lòng điền đầy đủ thông tin." });
    }

    try {
      await client
        .post("api/tickets", {
          json: { student_id, class_id, type, reason },
        })
        .json();
      return { success: true, message: "Gửi đơn thành công!" };
    } catch (e: any) {
      console.error("Failed to create ticket:", e);
      const body = await e.response?.json().catch(() => null);
      return fail(e.response?.status ?? 500, {
        message: body?.message ?? "Đã xảy ra lỗi. Vui lòng thử lại.",
      });
    }
  },
};
