<script lang="ts">
    import { SvelteMap } from "svelte/reactivity";
    import { enhance } from "$app/forms";
    import { showToast } from "$lib/toastStore";

    type Student = {
        id: string;
        first_name: string;
        last_name: string;
        class_id: number;
        class_name: string | null;
    };

    type ClassData = {
        id: number;
        name: string;
    };

    let { data }: { data: { students: Student[]; classes: ClassData[] } } =
        $props();

    let loadingStates = new SvelteMap<string, boolean>();
    let editingStudent = $state<Student | null>(null);
    let studentToDelete = $state<Student | null>(null);

    let editDialog: HTMLDialogElement;
    let deleteDialog: HTMLDialogElement;

    function isLoading(action: string): boolean {
        return loadingStates.get(action) ?? false;
    }

    function createEnhance(
        action: string,
        successMsg: string,
        onSuccess?: () => void,
    ) {
        return () => {
            loadingStates.set(action, true);

            return async ({ result, update }) => {
                loadingStates.set(action, false);

                if (result.type === "success") {
                    showToast({ message: successMsg, type: "success" });
                    onSuccess?.();
                    await update({ reset: action === "create" });
                } else if (result.type === "failure") {
                    showToast({
                        message: result.data?.message || "Action failed.",
                        type: "error",
                    });
                }
            };
        };
    }

    function openEditModal(student: Student) {
        editingStudent = { ...student };
        editDialog?.showModal();
    }

    function openDeleteModal(student: Student) {
        studentToDelete = student;
        deleteDialog?.showModal();
    }

    // Derived stats
    let studentsByClass = $derived(
        data.students.reduce(
            (acc, student) => {
                const className = student.class_name || "Unassigned";
                acc[className] = (acc[className] || 0) + 1;
                return acc;
            },
            {} as Record<string, number>,
        ),
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
                        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                    />
                </svg>
            </div>
            Student Management
        </h1>
        <p class="text-base-content/70 mt-2">
            Add and manage student records and class assignments.
        </p>
    </div>

    <!-- Stats -->
    {#if data.students.length > 0}
        <div
            class="stats stats-vertical lg:stats-horizontal shadow-lg mb-8 w-full border border-base-300"
        >
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
                            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                        />
                    </svg>
                </div>
                <div class="stat-title">Total Students</div>
                <div class="stat-value text-primary">
                    {data.students.length}
                </div>
                <div class="stat-desc">
                    Across {Object.keys(studentsByClass).length}
                    {Object.keys(studentsByClass).length === 1
                        ? "class"
                        : "classes"}
                </div>
            </div>

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
                            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                        />
                    </svg>
                </div>
                <div class="stat-title">Classes</div>
                <div class="stat-value text-secondary">
                    {data.classes.length}
                </div>
                <div class="stat-desc">Available classes</div>
            </div>
        </div>
    {/if}

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Add Student Form -->
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
                                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                            />
                        </svg>
                        Add New Student
                    </h2>
                    <div class="divider my-2"></div>

                    <form
                        class="space-y-4"
                        method="POST"
                        action="?/createStudent"
                        use:enhance={createEnhance(
                            "create",
                            "Student added successfully!",
                        )}
                    >
                        <div class="form-control">
                            <label for="id" class="label">
                                <span class="label-text font-medium"
                                    >Student ID</span
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
                                    id="id"
                                    name="id"
                                    class="input input-bordered w-full pl-10"
                                    placeholder="e.g., S12345"
                                    required
                                    disabled={isLoading("create")}
                                />
                            </div>
                        </div>

                        <div class="form-control">
                            <label for="first_name" class="label">
                                <span class="label-text font-medium"
                                    >First Name</span
                                >
                            </label>
                            <input
                                type="text"
                                id="first_name"
                                name="first_name"
                                class="input input-bordered"
                                autocomplete="given-name"
                                required
                                disabled={isLoading("create")}
                            />
                        </div>

                        <div class="form-control">
                            <label for="last_name" class="label">
                                <span class="label-text font-medium"
                                    >Last Name</span
                                >
                            </label>
                            <input
                                type="text"
                                id="last_name"
                                name="last_name"
                                class="input input-bordered"
                                autocomplete="family-name"
                                required
                                disabled={isLoading("create")}
                            />
                        </div>

                        <div class="form-control">
                            <label for="classId" class="label">
                                <span class="label-text font-medium">Class</span
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
                                            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                                        />
                                    </svg>
                                </span>
                                <select
                                    id="classId"
                                    name="classId"
                                    class="select select-bordered w-full pl-10"
                                    required
                                    disabled={isLoading("create")}
                                >
                                    <option value="">Select a class</option>
                                    {#each data.classes as cls}
                                        <option value={cls.id}
                                            >{cls.name}</option
                                        >
                                    {/each}
                                </select>
                            </div>
                        </div>

                        <button
                            type="submit"
                            class="btn btn-primary w-full mt-6"
                            disabled={isLoading("create")}
                        >
                            {#if isLoading("create")}
                                <span class="loading loading-spinner loading-sm"
                                ></span>
                                Adding...
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
                                Add Student
                            {/if}
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Student List -->
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
                            Existing Students
                        </h2>
                        <div class="badge badge-neutral badge-lg gap-2">
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
                                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                                />
                            </svg>
                            {data.students.length}
                        </div>
                    </div>

                    <div class="divider my-2"></div>

                    {#if data.students.length === 0}
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
                                <p class="font-medium">No students found</p>
                                <p class="text-sm opacity-80">
                                    Add your first student using the form.
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
                                        <th class="bg-base-200">Class</th>
                                        <th class="bg-base-200 text-right"
                                            >Actions</th
                                        >
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each data.students as student (student.id)}
                                        <tr
                                            class="hover:bg-base-200/50 transition-colors"
                                        >
                                            <td>
                                                <span
                                                    class="badge badge-ghost font-mono text-xs"
                                                >
                                                    {student.id}
                                                </span>
                                            </td>
                                            <td>
                                                <div
                                                    class="flex items-center gap-3"
                                                >
                                                    <span class="font-medium">
                                                        {student.first_name}
                                                        {student.last_name}
                                                    </span>
                                                </div>
                                            </td>
                                            <td>
                                                <span
                                                    class="badge badge-outline"
                                                >
                                                    {student.class_name ||
                                                        "N/A"}
                                                </span>
                                            </td>
                                            <td>
                                                <div
                                                    class="flex justify-end gap-2"
                                                >
                                                    <button
                                                        class="btn btn-sm btn-ghost hover:btn-primary"
                                                        onclick={() =>
                                                            openEditModal(
                                                                student,
                                                            )}
                                                        aria-label="Edit {student.first_name} {student.last_name}"
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
                                                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                                            />
                                                        </svg>
                                                        Edit
                                                    </button>
                                                    <button
                                                        class="btn btn-sm btn-ghost hover:btn-error text-error"
                                                        onclick={() =>
                                                            openDeleteModal(
                                                                student,
                                                            )}
                                                        aria-label="Delete {student.first_name} {student.last_name}"
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
                                                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                            />
                                                        </svg>
                                                        Delete
                                                    </button>
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
        </div>
    </div>
</div>

<!-- Edit Student Modal -->
<dialog bind:this={editDialog} class="modal">
    <div class="modal-box max-w-md">
        <h3 class="font-bold text-xl mb-1 flex items-center gap-2">
            <div class="rounded-lg bg-primary/10 p-2">
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
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                </svg>
            </div>
            Edit Student
        </h3>
        <p class="text-sm text-base-content/60 mb-4">
            Update student information
        </p>

        {#if editingStudent}
            <form
                class="space-y-4"
                method="POST"
                action="?/updateStudent"
                use:enhance={createEnhance(
                    "update",
                    "Student updated successfully!",
                    () => editDialog?.close(),
                )}
            >
                <input type="hidden" name="id" value={editingStudent.id} />

                <div class="form-control">
                    <label for="edit_first_name" class="label">
                        <span class="label-text font-medium">First Name</span>
                    </label>
                    <input
                        type="text"
                        id="edit_first_name"
                        name="first_name"
                        class="input input-bordered"
                        bind:value={editingStudent.first_name}
                        autocomplete="given-name"
                        required
                        disabled={isLoading("update")}
                    />
                </div>

                <div class="form-control">
                    <label for="edit_last_name" class="label">
                        <span class="label-text font-medium">Last Name</span>
                    </label>
                    <input
                        type="text"
                        id="edit_last_name"
                        name="last_name"
                        class="input input-bordered"
                        bind:value={editingStudent.last_name}
                        autocomplete="family-name"
                        required
                        disabled={isLoading("update")}
                    />
                </div>

                <div class="form-control">
                    <label for="edit_classId" class="label">
                        <span class="label-text font-medium">Class</span>
                    </label>
                    <select
                        id="edit_classId"
                        name="classId"
                        class="select select-bordered"
                        bind:value={editingStudent.class_id}
                        required
                        disabled={isLoading("update")}
                    >
                        {#each data.classes as cls}
                            <option value={cls.id}>{cls.name}</option>
                        {/each}
                    </select>
                </div>

                <div class="flex justify-end gap-2 pt-4">
                    <button
                        type="button"
                        class="btn btn-ghost"
                        onclick={() => editDialog?.close()}
                        disabled={isLoading("update")}
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        class="btn btn-primary"
                        disabled={isLoading("update")}
                    >
                        {#if isLoading("update")}
                            <span class="loading loading-spinner loading-sm"
                            ></span>
                            Updating...
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
                                    d="M5 13l4 4L19 7"
                                />
                            </svg>
                            Update
                        {/if}
                    </button>
                </div>
            </form>
        {/if}
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>

<!-- Delete Confirmation Modal -->
<dialog bind:this={deleteDialog} class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg">Confirm Deletion</h3>
        {#if studentToDelete}
            <div class="alert alert-warning mt-4">
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
                <div>
                    <p class="font-medium">Are you sure?</p>
                    <p class="text-sm">
                        Delete {studentToDelete.first_name}
                        {studentToDelete.last_name}? This cannot be undone.
                    </p>
                </div>
            </div>

            <form
                method="POST"
                action="?/deleteStudent"
                use:enhance={createEnhance(
                    "delete",
                    "Student deleted successfully!",
                    () => deleteDialog?.close(),
                )}
            >
                <input type="hidden" name="id" value={studentToDelete.id} />

                <div class="flex justify-end gap-2 mt-6">
                    <button
                        type="button"
                        class="btn btn-ghost"
                        onclick={() => deleteDialog?.close()}
                        disabled={isLoading("delete")}
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        class="btn btn-error"
                        disabled={isLoading("delete")}
                    >
                        {#if isLoading("delete")}
                            <span class="loading loading-spinner loading-sm"
                            ></span>
                            Deleting...
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
                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                />
                            </svg>
                            Delete
                        {/if}
                    </button>
                </div>
            </form>
        {/if}
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
