<script lang="ts">
    import { SvelteMap } from "svelte/reactivity";
    import { enhance } from "$app/forms";
    import { showToast } from "$lib/toastStore";

    type Teacher = {
        id: number;
        first_name: string;
        last_name: string;
        email: string;
        username: string;
    };

    let { data }: { data: { teachers: Teacher[] } } = $props();

    let loadingStates = new SvelteMap<string, boolean>();
    let editingTeacher = $state<Teacher | null>(null);
    let editDialog: HTMLDialogElement;

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

    function openEditModal(teacher: Teacher) {
        editingTeacher = { ...teacher };
        editDialog?.showModal();
    }
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
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                    />
                </svg>
            </div>
            Manage Teachers
        </h1>
        <p class="text-base-content/70 mt-2">
            Create and manage teacher accounts for your institution.
        </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Create Teacher Form -->
        <div class="lg:col-span-1">
            <div class="card bg-base-100 shadow-xl border border-base-300">
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
                        Create New Teacher
                    </h2>
                    <div class="divider my-2"></div>

                    <form
                        method="POST"
                        action="?/createTeacher"
                        class="space-y-4"
                        use:enhance={createEnhance(
                            "create",
                            "Teacher created successfully!",
                        )}
                    >
                        <div class="form-control">
                            <label for="email" class="label">
                                <span class="label-text font-medium"
                                    >Email Address</span
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
                                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                        />
                                    </svg>
                                </span>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    class="input input-bordered w-full pl-10"
                                    placeholder="teacher@school.edu"
                                    autocomplete="email"
                                    required
                                    disabled={isLoading("create")}
                                />
                            </div>
                        </div>

                        <div class="form-control">
                            <label for="username" class="label">
                                <span class="label-text font-medium"
                                    >Username</span
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
                                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                                        />
                                    </svg>
                                </span>
                                <input
                                    type="text"
                                    id="username"
                                    name="username"
                                    class="input input-bordered w-full pl-10"
                                    placeholder="username"
                                    autocomplete="username"
                                    required
                                    disabled={isLoading("create")}
                                />
                            </div>
                        </div>

                        <div class="form-control">
                            <label for="password" class="label">
                                <span class="label-text font-medium"
                                    >Password</span
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
                                            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                                        />
                                    </svg>
                                </span>
                                <input
                                    type="password"
                                    id="password"
                                    name="password"
                                    class="input input-bordered w-full pl-10"
                                    placeholder="••••••••"
                                    autocomplete="new-password"
                                    minlength="8"
                                    required
                                    disabled={isLoading("create")}
                                />
                            </div>
                            <div class="mt-1 text-xs text-base-content/60 pl-1">
                                Minimum 8 characters required
                            </div>
                        </div>

                        <div class="divider my-2 text-xs">
                            Personal Information
                        </div>

                        <div class="grid grid-cols-2 gap-3">
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
                        </div>

                        <button
                            type="submit"
                            class="btn btn-primary w-full mt-6"
                            disabled={isLoading("create")}
                        >
                            {#if isLoading("create")}
                                <span class="loading loading-spinner loading-sm"
                                ></span>
                                Creating Teacher...
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
                                Create Teacher
                            {/if}
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Teacher List -->
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
                                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                />
                            </svg>
                            Existing Teachers
                        </h2>
                        <div class="badge badge-primary badge-lg gap-2">
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
                            {data.teachers.length}
                        </div>
                    </div>

                    <div class="divider my-2"></div>

                    {#if data.teachers.length === 0}
                        <div class="alert">
                            <svg
                                class="h-6 w-6 shrink-0"
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
                                <p class="font-medium">No teachers found</p>
                                <p class="text-sm opacity-80">
                                    Create your first teacher account using the
                                    form.
                                </p>
                            </div>
                        </div>
                    {:else}
                        <div class="overflow-x-auto">
                            <table class="table table-zebra">
                                <thead>
                                    <tr class="border-b-2 border-base-300">
                                        <th class="bg-base-200">
                                            <span
                                                class="flex items-center gap-2"
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
                                                        d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
                                                    />
                                                </svg>
                                                ID
                                            </span>
                                        </th>
                                        <th class="bg-base-200">Name</th>
                                        <th class="bg-base-200">Email</th>
                                        <th class="bg-base-200">Username</th>
                                        <th class="bg-base-200 text-right"
                                            >Actions</th
                                        >
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each data.teachers as teacher (teacher.id)}
                                        <tr
                                            class="hover:bg-base-200/50 transition-colors"
                                        >
                                            <td>
                                                <span
                                                    class="badge badge-ghost badge-sm font-mono"
                                                >
                                                    {teacher.id}
                                                </span>
                                            </td>
                                            <td>
                                                <div
                                                    class="flex items-center gap-2"
                                                >
                                                    <span class="font-medium">
                                                        {teacher.first_name}
                                                        {teacher.last_name}
                                                    </span>
                                                </div>
                                            </td>
                                            <td class="text-sm">
                                                <div
                                                    class="flex items-center gap-2 text-base-content/70"
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
                                                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                                        />
                                                    </svg>
                                                    {teacher.email}
                                                </div>
                                            </td>
                                            <td>
                                                <span
                                                    class="badge badge-outline font-mono text-xs"
                                                >
                                                    {teacher.username}
                                                </span>
                                            </td>
                                            <td>
                                                <div class="flex justify-end">
                                                    <button
                                                        class="btn btn-sm btn-ghost hover:btn-primary"
                                                        onclick={() =>
                                                            openEditModal(
                                                                teacher,
                                                            )}
                                                        aria-label="Edit {teacher.first_name} {teacher.last_name}"
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

<!-- Edit Teacher Modal -->
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
            Edit Teacher
        </h3>
        <p class="text-sm text-base-content/60 mb-4">
            Update teacher account information
        </p>

        {#if editingTeacher}
            <form
                class="space-y-4"
                method="POST"
                action="?/updateTeacher"
                use:enhance={createEnhance(
                    "update",
                    "Teacher updated successfully!",
                    () => editDialog?.close(),
                )}
            >
                <input type="hidden" name="id" value={editingTeacher.id} />

                <div class="form-control">
                    <label for="edit_email" class="label">
                        <span class="label-text font-medium">Email Address</span
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
                                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                />
                            </svg>
                        </span>
                        <input
                            type="email"
                            id="edit_email"
                            name="email"
                            class="input input-bordered w-full pl-10"
                            bind:value={editingTeacher.email}
                            autocomplete="email"
                            required
                            disabled={isLoading("update")}
                        />
                    </div>
                </div>

                <div class="form-control">
                    <label for="edit_username" class="label">
                        <span class="label-text font-medium">Username</span>
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
                                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                                />
                            </svg>
                        </span>
                        <input
                            type="text"
                            id="edit_username"
                            name="username"
                            class="input input-bordered w-full pl-10"
                            bind:value={editingTeacher.username}
                            autocomplete="username"
                            required
                            disabled={isLoading("update")}
                        />
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div class="form-control">
                        <label for="edit_first_name" class="label">
                            <span class="label-text font-medium"
                                >First Name</span
                            >
                        </label>
                        <input
                            type="text"
                            id="edit_first_name"
                            name="first_name"
                            class="input input-bordered"
                            bind:value={editingTeacher.first_name}
                            autocomplete="given-name"
                            required
                            disabled={isLoading("update")}
                        />
                    </div>

                    <div class="form-control">
                        <label for="edit_last_name" class="label">
                            <span class="label-text font-medium">Last Name</span
                            >
                        </label>
                        <input
                            type="text"
                            id="edit_last_name"
                            name="last_name"
                            class="input input-bordered"
                            bind:value={editingTeacher.last_name}
                            autocomplete="family-name"
                            required
                            disabled={isLoading("update")}
                        />
                    </div>
                </div>

                <div class="divider my-2 text-xs">
                    Change Password (Optional)
                </div>

                <div class="form-control">
                    <label for="edit_password" class="label">
                        <span class="label-text font-medium">New Password</span>
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
                                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                                />
                            </svg>
                        </span>
                        <input
                            type="password"
                            id="edit_password"
                            name="password"
                            class="input input-bordered w-full pl-10"
                            placeholder="Leave blank to keep current"
                            autocomplete="new-password"
                            minlength="8"
                            disabled={isLoading("update")}
                        />
                    </div>
                    <div class="mt-1 text-xs text-base-content/60 pl-1">
                        Only fill this field if you want to change the password
                    </div>
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
                            Update Teacher
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
