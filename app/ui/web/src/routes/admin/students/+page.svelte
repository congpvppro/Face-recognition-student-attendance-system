<script lang="ts">
  import { SvelteMap } from "svelte/reactivity";
  import { enhance } from "$app/forms";
  import { showToast } from "$lib/toastStore";
  import {
    GraduationCap,
    School,
    Search,
    UserPlus,
    Pencil,
    Trash2,
    Users,
    X,
    ChevronDown,
    Filter,
  } from "lucide-svelte";

  type Student = {
    id: string;
    name: string;
    first_name: string | null;
    last_name: string | null;
    class_id: number;
    class_name: string | null;
    face_registered: number | null;
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

  // Search and filter state
  let searchQuery = $state("");
  let selectedClassFilter = $state<number | "all">("all");
  let addDialog: HTMLDialogElement;
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
          if (action === "create") showAddForm = false;
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

  // Helper to get display name
  function getDisplayName(student: Student): string {
    if (student.first_name && student.last_name) {
      return `${student.first_name} ${student.last_name}`;
    }
    return student.name || student.id;
  }

  // Filtered students based on search and class filter
  let filteredStudents = $derived.by(() => {
    let result = data.students;

    // Filter by class
    if (selectedClassFilter !== "all") {
      result = result.filter((s) => s.class_id === selectedClassFilter);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter(
        (s) =>
          s.id.toLowerCase().includes(query) ||
          (s.name && s.name.toLowerCase().includes(query)) ||
          (s.first_name && s.first_name.toLowerCase().includes(query)) ||
          (s.last_name && s.last_name.toLowerCase().includes(query)) ||
          getDisplayName(s).toLowerCase().includes(query),
      );
    }

    return result;
  });

  // Derived stats
  let studentsByClass = $derived(
    data.students.reduce(
      (acc, student) => {
        const className = student.class_name || "Chưa phân lớp";
        acc[className] = (acc[className] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    ),
  );

  // Get initials for avatar
  function getInitials(student: Student): string {
    if (student.first_name && student.last_name) {
      return `${student.first_name[0] || ""}${student.last_name[0] || ""}`.toUpperCase();
    }
    if (student.name) {
      const parts = student.name.split(" ");
      if (parts.length >= 2) {
        return `${parts[0][0] || ""}${parts[parts.length - 1][0] || ""}`.toUpperCase();
      }
      return (student.name[0] || "").toUpperCase();
    }
    return student.id[0]?.toUpperCase() || "?";
  }

  // Get color class based on class_id for visual distinction
  function getAvatarColor(classId: number): string {
    const colors = [
      "bg-primary text-primary-content",
      "bg-secondary text-secondary-content",
      "bg-accent text-accent-content",
      "bg-info text-info-content",
      "bg-success text-success-content",
      "bg-warning text-warning-content",
    ];
    return colors[classId % colors.length];
  }
</script>

<svelte:head>
  <title>Quản lý học sinh - Attendde</title>
</svelte:head>

<div class="min-h-screen bg-base-200/50">
  <div class="container mx-auto p-4 md:p-8 max-w-7xl">
    <!-- Header -->
    <div
      class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8"
    >
      <div>
        <h1 class="text-3xl font-bold flex items-center gap-3">
          <div class="rounded-xl bg-primary p-2.5 shadow-lg">
            <GraduationCap class="h-7 w-7 text-primary-content" />
          </div>
          Quản lý học sinh
        </h1>
        <p class="text-base-content/60 mt-2">
          Quản lý hồ sơ học sinh và phân lớp trong hệ thống
        </p>
      </div>
      <button
        class="btn btn-primary gap-2 shadow-lg"
        onclick={() => addDialog?.showModal()}
      >
        <UserPlus class="h-5 w-5" />
        Thêm học sinh
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
        <div class="card-body p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-base-content/60 font-medium">
                Tổng học sinh
              </p>
              <p class="text-3xl font-bold text-primary mt-1">
                {data.students.length}
              </p>
            </div>
            <div class="rounded-xl bg-primary/10 p-3">
              <Users class="h-6 w-6 text-primary" />
            </div>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
        <div class="card-body p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-base-content/60 font-medium">Số lớp</p>
              <p class="text-3xl font-bold text-secondary mt-1">
                {data.classes.length}
              </p>
            </div>
            <div class="rounded-xl bg-secondary/10 p-3">
              <School class="h-6 w-6 text-secondary" />
            </div>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
        <div class="card-body p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-base-content/60 font-medium">
                Trung bình/lớp
              </p>
              <p class="text-3xl font-bold text-accent mt-1">
                {data.classes.length > 0
                  ? Math.round(data.students.length / data.classes.length)
                  : 0}
              </p>
            </div>
            <div class="rounded-xl bg-accent/10 p-3">
              <GraduationCap class="h-6 w-6 text-accent" />
            </div>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
        <div class="card-body p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-base-content/60 font-medium">
                Kết quả lọc
              </p>
              <p class="text-3xl font-bold text-info mt-1">
                {filteredStudents.length}
              </p>
            </div>
            <div class="rounded-xl bg-info/10 p-3">
              <Filter class="h-6 w-6 text-info" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-8">
      <!-- Student List -->
      <div>
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
                Danh sách học sinh
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
                  <p class="font-medium">Chưa có học sinh nào</p>
                  <p class="text-sm opacity-80">
                    Thêm học sinh đầu tiên bằng biểu mẫu bên cạnh.
                  </p>
                </div>
              </div>
            {:else}
              <div class="overflow-x-auto">
                <table class="table table-zebra">
                  <thead>
                    <tr class="border-b-2 border-base-300">
                      <th class="bg-base-200">Mã học sinh</th>
                      <th class="bg-base-200">Họ tên</th>
                      <th class="bg-base-200">Lớp</th>
                      <th class="bg-base-200">Khuôn mặt</th>
                      <th class="bg-base-200 text-right">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each filteredStudents as student (student.id)}
                      <tr class="hover:bg-base-200/50 transition-colors">
                        <td>
                          <span class="badge badge-ghost font-mono text-xs">
                            {student.id}
                          </span>
                        </td>
                        <td>
                          <div class="flex items-center gap-3">
                            <div
                              class={`avatar placeholder ${getAvatarColor(student.class_id)}`}
                            >
                              <div class="w-8 h-8 rounded-full">
                                <span class="text-xs"
                                  >{getInitials(student)}</span
                                >
                              </div>
                            </div>
                            <div>
                              <span class="font-medium">
                                {getDisplayName(student)}
                              </span>
                              {#if student.name && student.first_name && student.last_name}
                                <span
                                  class="text-xs text-base-content/50 block"
                                >
                                  {student.name}
                                </span>
                              {/if}
                            </div>
                          </div>
                        </td>
                        <td>
                          <span class="badge badge-outline">
                            {student.class_name || "Chưa phân lớp"}
                          </span>
                        </td>
                        <td>
                          {#if student.face_registered}
                            <span class="badge badge-success gap-1">
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
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                              Đã đăng ký
                            </span>
                          {:else}
                            <span class="badge badge-warning gap-1">
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
                                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                />
                              </svg>
                              Chưa đăng ký
                            </span>
                          {/if}
                        </td>
                        <td>
                          <div class="flex justify-end gap-2">
                            <a 
                              href="/student/{student.id}" 
                              class="btn btn-sm btn-ghost hover:btn-info hover:text-info"
                              title="Xem chi tiết"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              Profile
                            </a>

                            <button
                              class="btn btn-sm btn-ghost hover:btn-primary"
                              onclick={() => openEditModal(student)}
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
                              Sửa
                            </button>
                            <button
                              class="btn btn-sm btn-ghost hover:btn-error text-error"
                              onclick={() => openDeleteModal(student)}
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
                              Xóa
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
</div>

<!-- Add Student Modal -->
<dialog bind:this={addDialog} class="modal">
  <div class="modal-box max-w-md">
    <h3 class="font-bold text-xl mb-1 flex items-center gap-2">
      <div class="rounded-lg bg-primary/10 p-2">
        <UserPlus class="h-5 w-5 text-primary" />
      </div>
      Thêm học sinh mới
    </h3>
    <p class="text-sm text-base-content/60 mb-4">Điền thông tin học sinh mới</p>

    <form
      class="space-y-4"
      method="POST"
      action="?/createStudent"
      use:enhance={createEnhance("create", "Thêm học sinh thành công!", () =>
        addDialog?.close(),
      )}
    >
      <div class="form-control">
        <label for="add_id" class="label">
          <span class="label-text font-medium">Mã học sinh</span>
        </label>
        <input
          type="text"
          id="add_id"
          name="id"
          class="input input-bordered"
          placeholder="VD: HS12345"
          required
          disabled={isLoading("create")}
        />
      </div>

      <div class="form-control">
        <label for="add_first_name" class="label">
          <span class="label-text font-medium">Họ</span>
        </label>
        <input
          type="text"
          id="add_first_name"
          name="first_name"
          class="input input-bordered"
          autocomplete="given-name"
          required
          disabled={isLoading("create")}
        />
      </div>

      <div class="form-control">
        <label for="add_last_name" class="label">
          <span class="label-text font-medium">Tên</span>
        </label>
        <input
          type="text"
          id="add_last_name"
          name="last_name"
          class="input input-bordered"
          autocomplete="family-name"
          required
          disabled={isLoading("create")}
        />
      </div>

      <div class="form-control">
        <label for="add_classId" class="label">
          <span class="label-text font-medium">Lớp</span>
        </label>
        <select
          id="add_classId"
          name="classId"
          class="select select-bordered w-full"
          required
          disabled={isLoading("create")}
        >
          <option value="">Chọn lớp</option>
          {#each data.classes as cls}
            <option value={cls.id}>{cls.name}</option>
          {/each}
        </select>
      </div>

      <div class="flex justify-end gap-2 pt-4">
        <button
          type="button"
          class="btn btn-ghost"
          onclick={() => addDialog?.close()}
          disabled={isLoading("create")}
        >
          Hủy
        </button>
        <button
          type="submit"
          class="btn btn-primary"
          disabled={isLoading("create")}
        >
          {#if isLoading("create")}
            <span class="loading loading-spinner loading-sm"></span>
            Đang thêm...
          {:else}
            <UserPlus class="h-4 w-4" />
            Thêm học sinh
          {/if}
        </button>
      </div>
    </form>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>

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
      Sửa thông tin học sinh
    </h3>
    <p class="text-sm text-base-content/60 mb-4">Cập nhật thông tin học sinh</p>

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
            <span class="label-text font-medium">Họ</span>
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
            <span class="label-text font-medium">Tên</span>
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
            <span class="label-text font-medium">Lớp</span>
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
            Hủy
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            disabled={isLoading("update")}
          >
            {#if isLoading("update")}
              <span class="loading loading-spinner loading-sm"></span>
              Đang cập nhật...
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
              Cập nhật
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
    <h3 class="font-bold text-lg">Xác nhận xóa</h3>
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
          <p class="font-medium">Bạn có chắc chắn?</p>
          <p class="text-sm">
            Xóa {studentToDelete.first_name}
            {studentToDelete.last_name}? Hành động này không thể hoàn tác.
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
            Hủy
          </button>
          <button
            type="submit"
            class="btn btn-error"
            disabled={isLoading("delete")}
          >
            {#if isLoading("delete")}
              <span class="loading loading-spinner loading-sm"></span>
              Đang xóa...
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
              Xóa
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
