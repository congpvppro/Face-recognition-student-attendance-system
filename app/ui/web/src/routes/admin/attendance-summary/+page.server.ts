import { api } from '$lib/server/http';
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ url, locals, cookies }) => {
    const { user } = locals;

    // Admin only
    if (!user || user.role !== 'admin') {
        throw redirect(303, '/login');
    }

    const client = api({ locals, cookies } as any);

    try {
        // Get list of CSV files
        const filesRes = await client.get('api/attendance/csv-files').json<any>();

        // Get selected file or default to TOTAL_SUMMARY
        const selectedFile =
            url.searchParams.get('file') || 'student_attendance_TOTAL_SUMMARY.csv';

        // Load CSV data
        const dataRes = await client.get(`api/attendance/csv/${selectedFile}`).json<any>();

        return {
            csvFiles: filesRes.files || [],
            currentFile: selectedFile,
            data: dataRes.data || [],
            summary: dataRes.summary || { total_students: 0, avg_attendance: '0%', avg_sessions: 0 },
            headers: dataRes.headers || []
        };
    } catch (error) {
        console.error('Error loading CSV data:', error);
        return {
            csvFiles: [],
            currentFile: '',
            data: [],
            summary: { total_students: 0, avg_attendance: '0%', avg_sessions: 0 },
            headers: []
        };
    }
};
