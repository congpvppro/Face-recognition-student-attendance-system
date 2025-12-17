import { error, redirect } from '@sveltejs/kit';
import { api } from '$lib/server/http';
import type { PageServerLoad } from './$types';
export const load: PageServerLoad = async ({ params, locals, cookies }) => {
    const { user } = locals;

    if (!user) {
        throw redirect(303, '/login');
    }
    const studentId = params.id;

    // Create API client with proper event object for auth
    const client = api({ locals, cookies } as any);
    try {
        // Fetch all data in parallel
        const [profileRes, graphRes, analysisRes, interventionsRes, historyRes] =
            await Promise.all([
                client.get(`api/students/${studentId}/profile`).json<any>(),
                client.get(`api/students/${studentId}/graph-data?days_before=30`).json<any>(),
                client.get(`api/students/${studentId}/analysis?limit=5`).json<any>(),
                client.get(`api/students/${studentId}/interventions`).json<any>(),
                client.get(`api/students/${studentId}/attendance-history?page=1&page_size=20`).json<any>()
            ]);
        return {
            student: profileRes.student,
            statistics: profileRes.statistics,
            graphData: graphRes.graph_data,
            analysis: analysisRes.analysis,
            interventions: interventionsRes.interventions,
            attendanceHistory: historyRes.attendance_records,
            pagination: historyRes.pagination
        };
    } catch (e: any) {
        console.error('Failed to load student profile:', e);

        if (e.response?.status === 403) {
            throw error(403, 'Access denied');
        }
        if (e.response?.status === 404) {
            throw error(404, 'Student not found');
        }

        throw error(500, 'Failed to load student profile');
    }
};