<script lang="ts">
    type AttendanceRecord = {
        id: number;
        timestamp: string;
        student_id: string;
        first_name: string;
        last_name: string;
        class_name: string;
    };

    type ClassData = {
        id: number;
        name: string;
    };

    type Student = {
        id: string;
        first_name: string;
        last_name: string;
    };

    let {
        data,
    }: {
        data: {
            attendance: AttendanceRecord[];
            classes: ClassData[];
            absentStudents: Student[];
            filters: { classId: string | null; date: string | null };
        };
    } = $props();

    // Derived stats
    let totalPresent = $derived(data.attendance.length);
    let totalAbsent = $derived(data.absentStudents.length);
    let totalStudents = $derived(totalPresent + totalAbsent);
    let attendanceRate = $derived(
        totalStudents > 0 ? (totalPresent / totalStudents) * 100 : 0,
    );

    // Format date for display
    function formatDate(dateStr: string | null): string {
        if (!dateStr) return "All Time";
        const date = new Date(dateStr);
        return date.toLocaleDateString("en-US", {
            weekday: "short",
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    }

    // Format time
    function formatTime(timestamp: string): string {
        const date = new Date(timestamp);
        return date.toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    // Get selected class name
    let selectedClassName = $derived(
        data.filters.classId
            ? data.classes.find((c) => String(c.id) === data.filters.classId)
                  ?.name || "Unknown"
            : "All Classes",
    );

    // Check if filters are active
    let hasActiveFilters = $derived(
        data.filters.classId !== null || data.filters.date !== null,
    );
</script>

<div class="container mx-auto p-8 max-w-7xl">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold flex items-center gap-3">
            <div class="rounded-lg bg-primary p-2">
                <svg
                    class="h-8 w-8 text-primary-content"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                </svg>
            </div>
            Attendance Statistics
        </h1>
        <p class="text-base-content/70 mt-2">
            View and analyze attendance records for {selectedClassName}
            {#if data.filters.date}
                on {formatDate(data.filters.date)}
            {/if}
        </p>
    </div>

    <!-- Stats Cards -->
    {#if hasActiveFilters && totalStudents > 0}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <!-- Total Present -->
            <div class="stats shadow-lg border border-base-300">
                <div class="stat">
                    <div class="stat-figure text-success">
                        <svg
                            class="h-8 w-8"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                    </div>
                    <div class="stat-title">Present</div>
                    <div class="stat-value text-success">{totalPresent}</div>
                    <div class="stat-desc">Students checked in</div>
                </div>
            </div>

            <!-- Total Absent -->
            <div class="stats shadow-lg border border-base-300">
                <div class="stat">
                    <div class="stat-figure text-error">
                        <svg
                            class="h-8 w-8"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                    </div>
                    <div class="stat-title">Absent</div>
                    <div class="stat-value text-error">{totalAbsent}</div>
                    <div class="stat-desc">Students not checked in</div>
                </div>
            </div>

            <!-- Attendance Rate -->
            <div class="stats shadow-lg border border-base-300">
                <div class="stat">
                    <div class="stat-figure text-primary">
                        <svg
                            class="h-8 w-8"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                            />
                        </svg>
                    </div>
                    <div class="stat-title">Attendance Rate</div>
                    <div class="stat-value text-primary">
                        {attendanceRate.toFixed(1)}%
                    </div>
                    <div class="stat-desc">
                        {totalPresent} of {totalStudents} students
                    </div>
                </div>
            </div>
        </div>
    {/if}

    <!-- Filters -->
    <form
        method="GET"
        class="card bg-base-100 shadow-xl mb-8 border border-base-300"
    >
        <div class="card-body">
            <div class="flex items-center justify-between mb-4">
                <h2 class="card-title">
                    <svg
                        class="h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                        />
                    </svg>
                    Filters
                </h2>
                {#if hasActiveFilters}
                    <a href="?" class="btn btn-ghost btn-sm gap-2">
                        <svg
                            class="h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                        Clear
                    </a>
                {/if}
            </div>

            <div class="flex flex-wrap gap-4 items-end">
                <div class="form-control flex-1 min-w-[200px]">
                    <label for="classId" class="label">
                        <span class="label-text font-medium">Class</span>
                    </label>
                    <div class="relative">
                        <span
                            class="absolute inset-y-0 left-0 flex items-center pl-3 text-base-content/40"
                        >
                            <svg
                                class="h-5 w-5"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                                />
                            </svg>
                        </span>
                        <select
                            name="classId"
                            id="classId"
                            class="select select-bordered w-full pl-10"
                        >
                            <option value="">All Classes</option>
                            {#each data.classes as cls}
                                <option
                                    value={cls.id}
                                    selected={String(cls.id) ===
                                        data.filters.classId}
                                >
                                    {cls.name}
                                </option>
                            {/each}
                        </select>
                    </div>
                </div>

                <div class="form-control flex-1 min-w-[200px]">
                    <label for="date" class="label">
                        <span class="label-text font-medium">Date</span>
                    </label>
                    <div class="relative">
                        <span
                            class="absolute inset-y-0 left-0 flex items-center pl-3 text-base-content/40"
                        >
                            <svg
                                class="h-5 w-5"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                                />
                            </svg>
                        </span>
                        <input
                            type="date"
                            name="date"
                            id="date"
                            class="input input-bordered w-full pl-10"
                            value={data.filters.date || ""}
                        />
                    </div>
                </div>

                <button type="submit" class="btn btn-primary gap-2">
                    <svg
                        class="h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                    Apply Filters
                </button>
            </div>
        </div>
    </form>

    <!-- Attendance Records -->
    <div class="card bg-base-100 shadow-xl mb-8 border border-base-300">
        <div class="card-body">
            <div class="flex items-center justify-between mb-4">
                <h2 class="card-title">
                    <svg
                        class="h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                        />
                    </svg>
                    Attendance Records
                </h2>
                <div class="badge badge-neutral gap-2">
                    <svg
                        class="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                    </svg>
                    {data.attendance.length}
                </div>
            </div>

            {#if data.attendance.length === 0}
                <div class="alert">
                    <svg
                        class="h-6 w-6"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                    <div>
                        <p class="font-medium">No attendance records found</p>
                        <p class="text-sm opacity-80">
                            Try adjusting your filters or check back later
                        </p>
                    </div>
                </div>
            {:else}
                <div class="overflow-x-auto">
                    <table class="table table-zebra">
                        <thead>
                            <tr class="border-b-2 border-base-300">
                                <th class="bg-base-200">ID</th>
                                <th class="bg-base-200">Timestamp</th>
                                <th class="bg-base-200">Student</th>
                                <th class="bg-base-200">Class</th>
                            </tr>
                        </thead>
                        <tbody>
                            {#each data.attendance as record (record.id)}
                                <tr class="hover:bg-base-200/50">
                                    <td>
                                        <span
                                            class="badge badge-ghost badge-sm font-mono"
                                        >
                                            {record.id}
                                        </span>
                                    </td>
                                    <td>
                                        <div
                                            class="flex items-center gap-2 text-sm"
                                        >
                                            <svg
                                                class="h-4 w-4 text-base-content/50"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                            >
                                                <path
                                                    stroke-linecap="round"
                                                    stroke-linejoin="round"
                                                    stroke-width="2"
                                                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                                                />
                                            </svg>
                                            {formatTime(record.timestamp)}
                                        </div>
                                    </td>
                                    <td>
                                        <div class="flex items-center gap-3">
                                            <div>
                                                <div class="font-medium">
                                                    {record.first_name}
                                                    {record.last_name}
                                                </div>
                                                <div
                                                    class="text-sm opacity-70 font-mono"
                                                >
                                                    {record.student_id}
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="badge badge-outline">
                                            {record.class_name}
                                        </span>
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            {/if}
        </div>
    </div>

    <!-- Absent Students -->
    {#if data.filters.classId}
        <div class="card bg-base-100 shadow-xl border border-base-300">
            <div class="card-body">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="card-title text-error">
                        <svg
                            class="h-5 w-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            />
                        </svg>
                        Absent Students
                    </h2>
                    <div class="badge badge-error gap-2">
                        {data.absentStudents.length}
                    </div>
                </div>

                {#if data.absentStudents.length === 0}
                    <div class="alert alert-success">
                        <svg
                            class="h-6 w-6"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                        <div>
                            <p class="font-medium">Perfect attendance!</p>
                            <p class="text-sm opacity-80">
                                All students in this class are present
                            </p>
                        </div>
                    </div>
                {:else}
                    <div class="overflow-x-auto">
                        <table class="table table-zebra">
                            <thead>
                                <tr class="border-b-2 border-base-300">
                                    <th class="bg-base-200">Student ID</th>
                                    <th class="bg-base-200">Name</th>
                                </tr>
                            </thead>
                            <tbody>
                                {#each data.absentStudents as student (student.id)}
                                    <tr class="hover:bg-base-200/50">
                                        <td>
                                            <span
                                                class="badge badge-ghost font-mono"
                                            >
                                                {student.id}
                                            </span>
                                        </td>
                                        <td>
                                            <div
                                                class="flex items-center gap-3"
                                            >
                                                <div class="avatar placeholder">
                                                    <div
                                                        class="bg-error text-error-content rounded-full w-10"
                                                    >
                                                        <span class="text-xs">
                                                            {student
                                                                .first_name[0]}{student
                                                                .last_name[0]}
                                                        </span>
                                                    </div>
                                                </div>
                                                <span class="font-medium">
                                                    {student.first_name}
                                                    {student.last_name}
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                {/if}
            </div>
        </div>
    {/if}
</div>
