import { api } from "$lib/server/http";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async (event) => {
	const client = api(event);
	const classId = event.url.searchParams.get("classId");
	const date = event.url.searchParams.get("date");

	const params = new URLSearchParams();
	if (classId) params.append("classId", classId);
	if (date) params.append("date", date);

	try {
		const [attendance, classes, students] = await Promise.all([
			client.get(`api/attendance?${params.toString()}`).json<any[]>(),
			client.get("api/classes").json<any[]>(),
			client.get("api/students").json<any[]>(),
		]);

		let absentStudents: any[] = [];
		if (classId) {
			const allStudentsInClass = students.filter(
				(s: any) => String(s.class_id) === classId,
			);
			const presentStudentIds = new Set(
				attendance.map((a: any) => a.student_id),
			);
			absentStudents = allStudentsInClass.filter(
				(s: any) => !presentStudentIds.has(s.id),
			);
		}

		return { attendance, classes, absentStudents, filters: { classId, date } };
	} catch (error) {
		console.error("Failed to load data:", error);
		return { attendance: [], classes: [], filters: { classId, date } };
	}
};
