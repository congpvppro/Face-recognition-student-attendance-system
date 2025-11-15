<script lang="ts">
    import { SvelteMap } from "svelte/reactivity";
    import { enhance } from "$app/forms";
    import { invalidateAll } from "$app/navigation";
    import { showToast } from "$lib/toastStore";

    type Student = { id: string; first_name: string; last_name: string };
    type Teacher = { id: number; first_name: string; last_name: string };
    type ClassData = {
        id: number;
        name: string;
        teacher: string | null;
        students: Student[];
    };

    let { data }: { data: { classes: ClassData[]; teachers: Teacher[] } } =
        $props();

    let expanded = new SvelteMap<number, boolean>();
    let isSubmitting = $state(false);

    function toggle(id: number) {
        expanded.set(id, !expanded.get(id));
    }

    function createEnhance() {
        return () => {
            isSubmitting = true;

            return async ({ result, update }) => {
                isSubmitting = false;

                if (result.type === "success") {
                    showToast({
                        message: "Class created successfully!",
                        type: "success",
                    });
                    await invalidateAll();
                    await update({ reset: true });
                } else if (result.type === "failure") {
                    showToast({
                        message:
                            result.data?.message || "Failed to create class.",
                        type: "error",
                    });
                }
            };
        };
    }

    // Derived stats
    let totalClasses = $derived(data.classes.length);
    let totalStudentsEnrolled = $derived(
        data.classes.reduce((sum, cls) => sum + cls.students.length, 0),
    );
    let averageClassSize = $derived(
        totalClasses > 0
            ? (totalStudentsEnrolled / totalClasses).toFixed(1)
            : 0,
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
                        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                    />
                </svg>
            </div>
            Manage Classes
        </h1>
        <p class="text-base-content/70 mt-2">
            Create and manage classes with assigned teachers and students.
        </p>
    </div>

    <!-- Stats Cards -->
    {#if totalClasses > 0}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
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
                                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                            />
                        </svg>
                    </div>
                    <div class="stat-title">Total Classes</div>
                    <div class="stat-value text-primary">{totalClasses}</div>
                    <div class="stat-desc">Active classes</div>
                </div>
            </div>

            <div class="stats shadow-lg border border-base-300">
                <div class="stat">
                    <div class="stat-figure text-secondary">
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
                                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                            />
                        </svg>
                    </div>
                    <div class="stat-title">Total Students</div>
                    <div class="stat-value text-secondary">
                        {totalStudentsEnrolled}
                    </div>
                    <div class="stat-desc">Across all classes</div>
                </div>
            </div>

            <div class="stats shadow-lg border border-base-300">
                <div class="stat">
                    <div class="stat-figure text-accent">
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
                                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                            />
                        </svg>
                    </div>
                    <div class="stat-title">Average Size</div>
                    <div class="stat-value text-accent">{averageClassSize}</div>
                    <div class="stat-desc">Students per class</div>
                </div>
            </div>
        </div>
    {/if}

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Create Class Form -->
        <div class="lg:col-span-1">
            <div
                class="card bg-base-100 shadow-xl border border-base-300 sticky top-8"
            >
                <div class="card-body">
                    <h2 class="card-title text-xl">
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
                                d="M12 4v16m8-8H4"
                            />
                        </svg>
                        Create New Class
                    </h2>
                    <div class="divider my-2"></div>

                    <form
                        method="POST"
                        action="?/createClass"
                        class="space-y-4"
                        use:enhance={createEnhance()}
                    >
                        <div class="form-control">
                            <label for="name" class="label">
                                <span class="label-text font-medium"
                                    >Class Name</span
                                >
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
                                            d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                                        />
                                    </svg>
                                </span>
                                <input
                                    type="text"
                                    id="name"
                                    name="name"
                                    class="input input-bordered w-full pl-10"
                                    placeholder="e.g., Computer Science 101"
                                    required
                                    disabled={isSubmitting}
                                />
                            </div>
                        </div>

                        <div class="form-control">
                            <label for="teacher_id" class="label">
                                <span class="label-text font-medium"
                                    >Assign Teacher</span
                                >
                            </label>
                            <div class="relative">
                                <span
                                    class="absolute inset-y-0 left-0 flex items-center pl-3 text-base-content/40 pointer-events-none z-10"
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
                                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                                        />
                                    </svg>
                                </span>
                                <select
                                    id="teacher_id"
                                    name="teacher_id"
                                    class="select select-bordered w-full pl-10"
                                    required
                                    disabled={isSubmitting}
                                >
                                    <option value="">Select a teacher</option>
                                    {#each data.teachers as teacher}
                                        <option value={teacher.id}>
                                            {teacher.first_name}
                                            {teacher.last_name}
                                        </option>
                                    {/each}
                                </select>
                            </div>
                        </div>

                        <button
                            type="submit"
                            class="btn btn-primary w-full mt-6"
                            disabled={isSubmitting}
                        >
                            {#if isSubmitting}
                                <span class="loading loading-spinner loading-sm"
                                ></span>
                                Creating...
                            {:else}
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
                                        d="M12 4v16m8-8H4"
                                    />
                                </svg>
                                Create Class
                            {/if}
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Classes List -->
        <div class="lg:col-span-2">
            <div class="card bg-base-100 shadow-xl border border-base-300">
                <div class="card-body">
                    <div class="flex items-center justify-between mb-4">
                        <h2 class="card-title text-xl">
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
                                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                                />
                            </svg>
                            Existing Classes
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
                                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                                />
                            </svg>
                            {data.classes.length}
                        </div>
                    </div>

                    <div class="divider my-2"></div>

                    {#if data.classes.length === 0}
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
                                <p class="font-medium">No classes found</p>
                                <p class="text-sm opacity-80">
                                    Create your first class using the form.
                                </p>
                            </div>
                        </div>
                    {:else}
                        <div class="space-y-4">
                            {#each data.classes as cls (cls.id)}
                                <div
                                    class="card bg-base-200 border border-base-300 transition-all hover:shadow-md"
                                >
                                    <div class="card-body p-4">
                                        <div
                                            class="flex items-center justify-between"
                                        >
                                            <div
                                                class="flex items-center gap-4 flex-1"
                                            >
                                                <div class="flex-1">
                                                    <h3
                                                        class="font-bold text-lg"
                                                    >
                                                        {cls.name}
                                                    </h3>
                                                    <div
                                                        class="flex items-center gap-2 text-sm text-base-content/70 mt-1"
                                                    >
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
                                                                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                                                            />
                                                        </svg>
                                                        <span
                                                            >{cls.teacher ||
                                                                "No teacher assigned"}</span
                                                        >
                                                    </div>
                                                </div>
                                            </div>

                                            <div
                                                class="flex items-center gap-3"
                                            >
                                                <div class="text-center">
                                                    <div
                                                        class="badge badge-lg gap-2"
                                                    >
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
                                                                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                                                            />
                                                        </svg>
                                                        {cls.students.length}
                                                    </div>
                                                    <div
                                                        class="text-xs text-base-content/60 mt-1"
                                                    >
                                                        {cls.students.length ===
                                                        1
                                                            ? "student"
                                                            : "students"}
                                                    </div>
                                                </div>

                                                <button
                                                    type="button"
                                                    class="btn btn-sm btn-ghost gap-2"
                                                    onclick={() =>
                                                        toggle(cls.id)}
                                                >
                                                    {#if expanded.get(cls.id)}
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
                                                                d="M5 15l7-7 7 7"
                                                            />
                                                        </svg>
                                                        Hide
                                                    {:else}
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
                                                                d="M19 9l-7 7-7-7"
                                                            />
                                                        </svg>
                                                        View
                                                    {/if}
                                                </button>
                                            </div>
                                        </div>

                                        <!-- Expandable Student List -->
                                        {#if expanded.get(cls.id)}
                                            <div
                                                class="mt-4 pt-4 border-t border-base-300"
                                            >
                                                <div
                                                    class="flex items-center gap-2 mb-3"
                                                >
                                                    <svg
                                                        class="h-5 w-5 text-primary"
                                                        fill="none"
                                                        viewBox="0 0 24 24"
                                                        stroke="currentColor"
                                                    >
                                                        <path
                                                            stroke-linecap="round"
                                                            stroke-linejoin="round"
                                                            stroke-width="2"
                                                            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                                                        />
                                                    </svg>
                                                    <h4 class="font-semibold">
                                                        Enrolled Students
                                                    </h4>
                                                </div>

                                                {#if cls.students.length === 0}
                                                    <div
                                                        class="alert alert-warning"
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
                                                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                                            />
                                                        </svg>
                                                        <span class="text-sm"
                                                            >No students
                                                            enrolled in this
                                                            class yet.</span
                                                        >
                                                    </div>
                                                {:else}
                                                    <div
                                                        class="grid grid-cols-1 md:grid-cols-2 gap-2"
                                                    >
                                                        {#each cls.students as student}
                                                            <div
                                                                class="flex items-center gap-3 p-2 rounded-lg bg-base-100 hover:bg-base-300 transition-colors"
                                                            >
                                                                <div>
                                                                    <div
                                                                        class="font-medium"
                                                                    >
                                                                        {student.first_name}
                                                                        {student.last_name}
                                                                    </div>
                                                                    <div
                                                                        class="text-xs opacity-70 font-mono"
                                                                    >
                                                                        {student.id}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        {/each}
                                                    </div>
                                                {/if}
                                            </div>
                                        {/if}
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    </div>
</div>
