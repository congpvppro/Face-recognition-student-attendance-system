<script lang="ts">
    import { onMount } from "svelte";
    import { SvelteMap } from "svelte/reactivity";
    import { enhance } from "$app/forms";
    import { invalidateAll } from "$app/navigation";
    import { showToast } from "$lib/toastStore";
    import type { SubmitFunction } from "./$types";

    type UnregisteredFace = {
        face_id: string;
        class_id: number;
    };

    type Student = {
        id: string;
        first_name: string;
        last_name: string;
        class_id: number;
    };

    let {
        data,
    }: {
        data: { unregisteredFaces: UnregisteredFace[]; students: Student[] };
    } = $props();

    // Reactive state using SvelteMap
    let activeTabs = new SvelteMap<string, "assign" | "create">();
    let loadingStates = new SvelteMap<string, boolean>();
    let imageErrors = new SvelteMap<string, boolean>();

    // Initialize tabs on mount
    onMount(() => {
        data.unregisteredFaces.forEach((face) => {
            activeTabs.set(face.face_id, "assign");
        });
    });

    // Get students for face's class
    function getStudentsForFace(face: UnregisteredFace): Student[] {
        return data.students.filter((s) => s.class_id === face.class_id);
    }

    function createEnhance(
        faceId: string,
        action: string,
        successMsg: string,
    ): SubmitFunction {
        const key = `${faceId}-${action}`;

        return ({ cancel }) => {
            if (loadingStates.get(key)) {
                cancel();
                return;
            }
            loadingStates.set(key, true);

            return async ({ result, update }) => {
                loadingStates.set(key, false);

                if (result.type === "success") {
                    showToast({ message: successMsg, type: "success" });

                    await invalidateAll();

                    await update();
                } else if (result.type === "failure") {
                    showToast({
                        message: result.data?.message || "Action failed.",
                        type: "error",
                    });
                }
            };
        };
    }
</script>

<div class="container mx-auto p-8">
    <div class="mb-6 flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Unregistered Faces</h1>
            <p class="mt-1 text-sm opacity-70">
                Assign faces to students or create new profiles.
            </p>
        </div>
        {#if data.unregisteredFaces.length > 0}
            <span class="badge badge-primary badge-lg">
                {data.unregisteredFaces.length}
            </span>
        {/if}
    </div>

    {#if data.unregisteredFaces.length === 0}
        <div class="alert alert-info">
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
            <span
                >No unregistered faces found. All faces have been processed!</span
            >
        </div>
    {:else}
        <div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {#each data.unregisteredFaces as face (face.face_id)}
                {@const students = getStudentsForFace(face)}
                {@const tab = activeTabs.get(face.face_id) ?? "assign"}
                {@const loading = (action: string) =>
                    loadingStates.get(`${face.face_id}-${action}`) ?? false}

                <!-- Added fade-out animation class -->
                <div
                    class="card bg-base-100 shadow-xl transition-all duration-300"
                >
                    <!-- Image -->
                    <figure class="relative bg-base-300">
                        {#if imageErrors.get(face.face_id)}
                            <div
                                class="flex aspect-square w-full items-center justify-center"
                            >
                                <svg
                                    class="h-16 w-16 opacity-50"
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
                            </div>
                        {:else}
                            <img
                                src={`/api/students/unregistered/image/${face.face_id}`}
                                alt="Face {face.face_id}"
                                class="aspect-square w-full object-cover"
                                loading="lazy"
                                onerror={() =>
                                    imageErrors.set(face.face_id, true)}
                            />
                        {/if}

                        <!-- Ignore button -->
                        <form
                            method="POST"
                            action="?/ignoreFace"
                            use:enhance={createEnhance(
                                face.face_id,
                                "ignore",
                                "Face ignored",
                            )}
                            class="absolute right-2 top-2"
                        >
                            <input
                                type="hidden"
                                name="faceId"
                                value={face.face_id}
                            />
                            <button
                                type="submit"
                                class="btn btn-circle btn-ghost btn-sm bg-base-100/70 hover:bg-error hover:text-error-content backdrop-blur-sm transition-colors"
                                aria-label="Ignore this face"
                                disabled={loading("ignore")}
                            >
                                {#if loading("ignore")}
                                    <span
                                        class="loading loading-spinner loading-xs"
                                    ></span>
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
                                            d="M6 18L18 6M6 6l12 12"
                                        />
                                    </svg>
                                {/if}
                            </button>
                        </form>
                    </figure>

                    <div class="card-body">
                        <!-- Tabs -->
                        <div class="tabs tabs-boxed" role="tablist">
                            <button
                                type="button"
                                role="tab"
                                class="tab"
                                class:tab-active={tab === "assign"}
                                onclick={() =>
                                    activeTabs.set(face.face_id, "assign")}
                                disabled={loading("assign") ||
                                    loading("create")}
                            >
                                Assign
                            </button>
                            <button
                                type="button"
                                role="tab"
                                class="tab"
                                class:tab-active={tab === "create"}
                                onclick={() =>
                                    activeTabs.set(face.face_id, "create")}
                                disabled={loading("assign") ||
                                    loading("create")}
                            >
                                Create
                            </button>
                        </div>

                        <!-- Tab Content -->
                        <div class="pt-4">
                            {#if tab === "assign"}
                                {#if students.length === 0}
                                    <div class="alert alert-warning">
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
                                            <p class="text-sm font-medium">
                                                No students in this class
                                            </p>
                                            <p class="text-xs opacity-80">
                                                Switch to "Create" tab to add a
                                                new student
                                            </p>
                                        </div>
                                    </div>
                                {:else}
                                    <form
                                        method="POST"
                                        action="?/assignStudent"
                                        use:enhance={createEnhance(
                                            face.face_id,
                                            "assign",
                                            "Student assigned!",
                                        )}
                                    >
                                        <input
                                            type="hidden"
                                            name="faceId"
                                            value={face.face_id}
                                        />

                                        <label
                                            for="student-{face.face_id}"
                                            class="label"
                                        >
                                            <span class="label-text font-medium"
                                                >Select Student</span
                                            >
                                        </label>
                                        <select
                                            name="studentId"
                                            id="student-{face.face_id}"
                                            class="select select-bordered w-full"
                                            required
                                            disabled={loading("assign")}
                                        >
                                            <option value=""
                                                >-- Select --</option
                                            >
                                            {#each students as student}
                                                <option value={student.id}>
                                                    {student.first_name}
                                                    {student.last_name} ({student.id})
                                                </option>
                                            {/each}
                                        </select>

                                        <button
                                            type="submit"
                                            class="btn btn-primary mt-4 w-full"
                                            disabled={loading("assign")}
                                        >
                                            {#if loading("assign")}
                                                <span
                                                    class="loading loading-spinner loading-sm"
                                                ></span>
                                                Assigning...
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
                                                Assign
                                            {/if}
                                        </button>
                                    </form>
                                {/if}
                            {:else}
                                <!-- Create form -->
                                <form
                                    method="POST"
                                    action="?/createAndAssignStudent"
                                    use:enhance={createEnhance(
                                        face.face_id,
                                        "create",
                                        "Student created!",
                                    )}
                                    class="space-y-3"
                                >
                                    <input
                                        type="hidden"
                                        name="faceId"
                                        value={face.face_id}
                                    />
                                    <input
                                        type="hidden"
                                        name="classId"
                                        value={face.class_id}
                                    />

                                    <div>
                                        <label
                                            for="sid-{face.face_id}"
                                            class="label"
                                        >
                                            <span class="label-text font-medium"
                                                >Student ID</span
                                            >
                                        </label>
                                        <input
                                            type="text"
                                            name="studentId"
                                            id="sid-{face.face_id}"
                                            class="input input-bordered w-full"
                                            placeholder="e.g., S12345"
                                            required
                                            disabled={loading("create")}
                                        />
                                    </div>

                                    <div>
                                        <label
                                            for="fname-{face.face_id}"
                                            class="label"
                                        >
                                            <span class="label-text font-medium"
                                                >First Name</span
                                            >
                                        </label>
                                        <input
                                            type="text"
                                            name="firstName"
                                            id="fname-{face.face_id}"
                                            class="input input-bordered w-full"
                                            required
                                            disabled={loading("create")}
                                        />
                                    </div>

                                    <div>
                                        <label
                                            for="lname-{face.face_id}"
                                            class="label"
                                        >
                                            <span class="label-text font-medium"
                                                >Last Name</span
                                            >
                                        </label>
                                        <input
                                            type="text"
                                            name="lastName"
                                            id="lname-{face.face_id}"
                                            class="input input-bordered w-full"
                                            required
                                            disabled={loading("create")}
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        class="btn btn-secondary mt-2 w-full"
                                        disabled={loading("create")}
                                    >
                                        {#if loading("create")}
                                            <span
                                                class="loading loading-spinner loading-sm"
                                            ></span>
                                            Creating...
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
                                                    d="M12 4v16m8-8H4"
                                                />
                                            </svg>
                                            Create & Assign
                                        {/if}
                                    </button>
                                </form>
                            {/if}
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>
