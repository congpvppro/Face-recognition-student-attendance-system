<script lang="ts">
  import { SvelteMap } from "svelte/reactivity";
  import { enhance } from "$app/forms";
  import { showToast } from "$lib/toastStore";

  type Parent = {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    username: string;
  };

  type Class = {
    id: number;
    name: string;
    students: { id: string; first_name: string; last_name: string }[];
  };

  type Link = {
    parent_id: number;
    student_id: string;
    first_name: string;
    last_name: string;
    class_id: number | null;
  };

  let {
    data,
  }: { data: { parents: Parent[]; classes: Class[]; links: Link[] } } =
    $props();

  let loadingStates = new SvelteMap<string, boolean>();
  let editingParent = $state<Parent | null>(null);
  let linkingParent = $state<Parent | null>(null);
  let editDialog: HTMLDialogElement;
  let linkDialog: HTMLDialogElement;

  // Linking Logic State
  let selectedClassId = $state<number | null>(null);
  let selectedStudentId = $state<string | null>(null);

  let filteredStudents = $derived.by(() => {
    if (!selectedClassId) return [];
    const selectedClass = data.classes.find((c) => c.id === selectedClassId);
    return selectedClass ? selectedClass.students : [];
  });

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
          await update({ reset: action === "create" || action === "link" });
          // Reset local state
          selectedClassId = null;
          selectedStudentId = null;
        } else if (result.type === "failure") {
          showToast({
            message: result.data?.message || "Action failed.",
            type: "error",
          });
        }
      };
    };
  }

  function openEditModal(parent: Parent) {
    editingParent = { ...parent };
    editDialog?.showModal();
  }

  function openLinkModal(parent: Parent) {
    linkingParent = { ...parent };
    selectedClassId = null;
    selectedStudentId = null;
    linkDialog?.showModal();
  }

  function getLinkedStudents(parentId: number) {
    return data.links.filter((l) => l.parent_id === parentId);
  }
</script>

<div class="container mx-auto p-8 max-w-7xl">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold flex items-center gap-3">
      <div class="rounded-lg bg-green-600 p-2">
        <svg
          class="h-8 w-8 text-white"
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
      Manage Parents
    </h1>
    <p class="text-base-content/70 mt-2">
      Create and manage parent accounts and link them to students.
    </p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <!-- Create Parent Form -->
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
            Create New Parent
          </h2>
          <div class="divider my-2"></div>

          <form
            method="POST"
            action="?/createParent"
            class="space-y-4"
            use:enhance={createEnhance(
              "create",
              "Parent created successfully!",
            )}
          >
            <div class="form-control">
              <label for="email" class="label">
                <span class="label-text font-medium">Email Address</span>
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
                  placeholder="parent@example.com"
                  autocomplete="email"
                  required
                  disabled={isLoading("create")}
                />
              </div>
            </div>

            <div class="form-control">
              <label for="username" class="label">
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
                <span class="label-text font-medium">Password</span>
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

            <div class="divider my-2 text-xs">Personal Information</div>

            <div class="grid grid-cols-2 gap-3">
              <div class="form-control">
                <label for="first_name" class="label">
                  <span class="label-text font-medium">First Name</span>
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
                  <span class="label-text font-medium">Last Name</span>
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
                <span class="loading loading-spinner loading-sm"></span>
                Creating Parent...
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
                Create Parent
              {/if}
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Parent List -->
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
              Existing Parents
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
              {data.parents.length}
            </div>
          </div>

          <div class="divider my-2"></div>

          {#if data.parents.length === 0}
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
                <p class="font-medium">No parents found</p>
                <p class="text-sm opacity-80">
                  Create your first parent account using the form.
                </p>
              </div>
            </div>
          {:else}
            <div class="overflow-x-auto">
              <table class="table table-zebra">
                <thead>
                  <tr class="border-b-2 border-base-300">
                    <th class="bg-base-200 w-16">ID</th>
                    <th class="bg-base-200">Parent Info</th>
                    <th class="bg-base-200">Linked Students</th>
                    <th class="bg-base-200 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {#each data.parents as parent (parent.id)}
                    <tr class="hover:bg-base-200/50 transition-colors">
                      <td class="align-top">
                        <span class="badge badge-ghost badge-sm font-mono">
                          {parent.id}
                        </span>
                      </td>
                      <td class="align-top">
                        <div>
                          <div class="font-medium text-base">
                            {parent.first_name}
                            {parent.last_name}
                          </div>
                          <div
                            class="text-xs text-base-content/60 flex flex-col gap-0.5 mt-1"
                          >
                            <span class="flex items-center gap-1">
                              @{parent.username}
                            </span>
                            <span class="flex items-center gap-1">
                              {parent.email}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td class="align-top">
                        <div class="flex flex-wrap gap-2">
                          {#each getLinkedStudents(parent.id) as link}
                            <div class="badge badge-outline gap-1 py-3 px-2">
                              <div class="avatar placeholder">
                                <div
                                  class="bg-neutral-focus text-neutral-content rounded-full w-4"
                                >
                                  <span class="text-[8px]"
                                    >{link.first_name[0]}</span
                                  >
                                </div>
                              </div>
                              <span class="font-medium"
                                >{link.first_name} {link.last_name}</span
                              >
                              {#if link.class_id}
                                <span class="text-[10px] opacity-60 ml-1"
                                  >(Class {link.class_id})</span
                                >
                              {/if}
                            </div>
                          {/each}
                          <button
                            class="btn btn-xs btn-ghost btn-circle border border-dashed border-base-content/30"
                            onclick={() => openLinkModal(parent)}
                            title="Add Student"
                          >
                            <svg
                              class="h-3 w-3"
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
                          </button>
                        </div>
                      </td>
                      <td class="align-top">
                        <div class="flex justify-end gap-2">
                          <button
                            class="btn btn-sm btn-ghost hover:btn-primary"
                            onclick={() => openEditModal(parent)}
                            aria-label="Edit {parent.first_name} {parent.last_name}"
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

<!-- Edit Parent Modal -->
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
      Edit Parent
    </h3>
    <p class="text-sm text-base-content/60 mb-4">
      Update parent account information
    </p>

    {#if editingParent}
      <form
        class="space-y-4"
        method="POST"
        action="?/updateParent"
        use:enhance={createEnhance(
          "update",
          "Parent updated successfully!",
          () => editDialog?.close(),
        )}
      >
        <input type="hidden" name="id" value={editingParent.id} />

        <div class="form-control">
          <label for="edit_email" class="label">
            <span class="label-text font-medium">Email Address</span>
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
              bind:value={editingParent.email}
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
              bind:value={editingParent.username}
              autocomplete="username"
              required
              disabled={isLoading("update")}
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="form-control">
            <label for="edit_first_name" class="label">
              <span class="label-text font-medium">First Name</span>
            </label>
            <input
              type="text"
              id="edit_first_name"
              name="first_name"
              class="input input-bordered"
              bind:value={editingParent.first_name}
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
              bind:value={editingParent.last_name}
              autocomplete="family-name"
              required
              disabled={isLoading("update")}
            />
          </div>
        </div>

        <div class="divider my-2 text-xs">Change Password (Optional)</div>

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
              <span class="loading loading-spinner loading-sm"></span>
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
              Update Parent
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

<!-- Link Student Modal -->
<dialog bind:this={linkDialog} class="modal">
  <div class="modal-box w-11/12 max-w-2xl">
    <h3 class="font-bold text-xl mb-4">Link Student to Parent</h3>

    {#if linkingParent}
      <form
        method="POST"
        action="?/linkStudent"
        use:enhance={createEnhance("link", "Student linked successfully!", () =>
          linkDialog?.close(),
        )}
        class="space-y-4"
      >
        <input type="hidden" name="parentId" value={linkingParent.id} />

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- 1. Select Class -->
          <div class="form-control">
            <label for="classSelect" class="label">
              <span class="label-text font-medium">1. Select Class</span>
            </label>
            <select
              id="classSelect"
              class="select select-bordered w-full"
              bind:value={selectedClassId}
              disabled={isLoading("link")}
            >
              <option value={null} disabled selected>Choose a class...</option>
              {#each data.classes as cls}
                <option value={cls.id}>{cls.name}</option>
              {/each}
            </select>
          </div>

          <!-- 2. Select Student -->
          <div class="form-control">
            <label for="studentSelect" class="label">
              <span class="label-text font-medium">2. Select Student</span>
            </label>
            <select
              name="studentId"
              id="studentSelect"
              class="select select-bordered w-full"
              bind:value={selectedStudentId}
              required
              disabled={!selectedClassId || isLoading("link")}
            >
              <option value={null} disabled selected>
                {!selectedClassId
                  ? "Select a class first"
                  : "Choose a student..."}
              </option>
              {#each filteredStudents as student}
                <option value={student.id}
                  >{student.first_name}
                  {student.last_name} ({student.id})</option
                >
              {/each}
            </select>
          </div>
        </div>

        <!-- Manual Entry Fallback -->
        <div class="divider text-xs text-base-content/50">
          OR ENTER MANUALLY
        </div>

        <div class="form-control">
          <label for="manualStudentId" class="label">
            <span class="label-text font-medium">Student ID (Manual)</span>
          </label>
          <input
            type="text"
            name="studentId"
            id="manualStudentId"
            class="input input-bordered w-full font-mono"
            placeholder="Enter ID directly if known"
            value={selectedStudentId || ""}
            oninput={(e) => (selectedStudentId = e.currentTarget.value)}
            disabled={isLoading("link")}
          />
        </div>

        <div class="modal-action">
          <button
            type="button"
            class="btn btn-ghost"
            onclick={() => linkDialog?.close()}
            disabled={isLoading("link")}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            disabled={isLoading("link") || !selectedStudentId}
          >
            {#if isLoading("link")}
              <span class="loading loading-spinner loading-sm"></span>
              Linking...
            {:else}
              Link Student
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
