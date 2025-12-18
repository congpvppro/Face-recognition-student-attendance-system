<script lang="ts">
  import { SvelteMap } from "svelte/reactivity";
  import { enhance } from "$app/forms";
  import { showToast } from "$lib/toastStore";
  import {
    Users,
    UserPlus,
    Search,
    X,
    Pencil,
    Link2,
    Mail,
    User,
    Lock,
    School,
    GraduationCap,
  } from "lucide-svelte";

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

  // Search and filter state
  let searchQuery = $state("");
  let showAddForm = $state(false);

  // Linking Logic State
  let selectedClassId = $state<number | null>(null);
  let selectedStudentId = $state<string | null>(null);

  let filteredStudents = $derived.by(() => {
    if (!selectedClassId) return [];
    const selectedClass = data.classes.find((c) => c.id === selectedClassId);
    return selectedClass ? selectedClass.students : [];
  });

  // Filtered parents based on search
  let filteredParents = $derived.by(() => {
    if (!searchQuery.trim()) return data.parents;
    const query = searchQuery.toLowerCase().trim();
    return data.parents.filter(
      (p) =>
        p.first_name.toLowerCase().includes(query) ||
        p.last_name.toLowerCase().includes(query) ||
        p.email.toLowerCase().includes(query) ||
        p.username.toLowerCase().includes(query) ||
        `${p.first_name} ${p.last_name}`.toLowerCase().includes(query),
    );
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

  // Get initials for avatar
  function getInitials(firstName: string, lastName: string): string {
    return `${firstName[0] || ""}${lastName[0] || ""}`.toUpperCase();
  }

  // Get total linked students
  let totalLinkedStudents = $derived(data.links.length);
</script>

<svelte:head>
  <title>Quản lý phụ huynh - Attendde</title>
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
            <Users class="h-7 w-7 text-primary-content" />
          </div>
          Quản lý phụ huynh
        </h1>
        <p class="text-base-content/60 mt-2">
          Tạo tài khoản phụ huynh và liên kết với học sinh
        </p>
      </div>
      <button
        class="btn btn-primary gap-2 shadow-lg"
        onclick={() => (showAddForm = !showAddForm)}
      >
        {#if showAddForm}
          <X class="h-5 w-5" />
          Đóng
        {:else}
          <UserPlus class="h-5 w-5" />
          Thêm phụ huynh
        {/if}
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
        <div class="card-body p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-base-content/60 font-medium">
                Tổng phụ huynh
              </p>
              <p class="text-3xl font-bold text-primary mt-1">
                {data.parents.length}
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
              <p class="text-sm text-base-content/60 font-medium">
                Học sinh liên kết
              </p>
              <p class="text-3xl font-bold text-secondary mt-1">
                {totalLinkedStudents}
              </p>
            </div>
            <div class="rounded-xl bg-secondary/10 p-3">
              <Link2 class="h-6 w-6 text-secondary" />
            </div>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
        <div class="card-body p-5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-base-content/60 font-medium">
                Kết quả tìm kiếm
              </p>
              <p class="text-3xl font-bold text-accent mt-1">
                {filteredParents.length}
              </p>
            </div>
            <div class="rounded-xl bg-accent/10 p-3">
              <Search class="h-6 w-6 text-accent" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Collapsible Add Parent Form -->
    {#if showAddForm}
      <div class="card bg-base-100 shadow-lg mb-8 border border-primary/20">
        <div class="card-body">
          <h2 class="card-title text-xl mb-4">
            <UserPlus class="h-5 w-5 text-primary" />
            Thêm phụ huynh mới
          </h2>

          <form
            method="POST"
            action="?/createParent"
            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            use:enhance={createEnhance("create", "Tạo phụ huynh thành công!")}
          >
            <div class="form-control">
              <label for="email" class="label">
                <span class="label-text font-medium">Email</span>
              </label>
              <div class="relative">
                <Mail
                  class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-base-content/40 z-10"
                />
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
                <span class="label-text font-medium">Tên đăng nhập</span>
              </label>
              <div class="relative">
                <User
                  class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-base-content/40 z-10"
                />
                <input
                  type="text"
                  id="username"
                  name="username"
                  class="input input-bordered w-full pl-10"
                  placeholder="tendangnhap"
                  autocomplete="username"
                  required
                  disabled={isLoading("create")}
                />
              </div>
            </div>

            <div class="form-control">
              <label for="password" class="label">
                <span class="label-text font-medium">Mật khẩu</span>
              </label>
              <div class="relative">
                <Lock
                  class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-base-content/40 z-10"
                />
                <input
                  type="password"
                  id="password"
                  name="password"
                  class="input input-bordered w-full pl-10"
                  placeholder="Tối thiểu 8 ký tự"
                  autocomplete="new-password"
                  minlength="8"
                  required
                  disabled={isLoading("create")}
                />
              </div>
            </div>

            <div class="form-control">
              <label for="first_name" class="label">
                <span class="label-text font-medium">Họ</span>
              </label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                class="input input-bordered"
                placeholder="Nguyễn Văn"
                autocomplete="given-name"
                required
                disabled={isLoading("create")}
              />
            </div>

            <div class="form-control">
              <label for="last_name" class="label">
                <span class="label-text font-medium">Tên</span>
              </label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                class="input input-bordered"
                placeholder="An"
                autocomplete="family-name"
                required
                disabled={isLoading("create")}
              />
            </div>

            <div class="flex items-end gap-2">
              <button
                type="button"
                class="btn btn-ghost"
                onclick={() => (showAddForm = false)}
              >
                Hủy
              </button>
              <button
                type="submit"
                class="btn btn-primary flex-1 gap-2"
                disabled={isLoading("create")}
              >
                {#if isLoading("create")}
                  <span class="loading loading-spinner loading-sm"></span>
                  Đang tạo...
                {:else}
                  <UserPlus class="h-4 w-4" />
                  Tạo phụ huynh
                {/if}
              </button>
            </div>
          </form>
        </div>
      </div>
    {/if}

    <!-- Search Bar -->
    <div class="card bg-base-100 shadow-md mb-6">
      <div class="card-body p-4">
        <div class="relative">
          <Search
            class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-base-content/40 z-10"
          />
          <input
            type="text"
            placeholder="Tìm kiếm theo tên, email, tên đăng nhập..."
            class="input input-bordered w-full pl-10 pr-10"
            bind:value={searchQuery}
          />
          {#if searchQuery}
            <button
              class="absolute right-3 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs btn-circle"
              onclick={() => (searchQuery = "")}
            >
              <X class="h-4 w-4" />
            </button>
          {/if}
        </div>
      </div>
    </div>

    <!-- Parent List -->
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body p-0">
        {#if data.parents.length === 0}
          <!-- Empty State -->
          <div class="flex flex-col items-center justify-center py-16 px-4">
            <div class="rounded-full bg-base-200 p-6 mb-4">
              <Users class="h-12 w-12 text-base-content/30" />
            </div>
            <h3 class="text-xl font-bold text-base-content/70 mb-2">
              Chưa có phụ huynh nào
            </h3>
            <p class="text-base-content/50 text-center max-w-md mb-6">
              Bắt đầu thêm tài khoản phụ huynh bằng cách nhấn nút "Thêm phụ
              huynh" ở trên.
            </p>
            <button
              class="btn btn-primary gap-2"
              onclick={() => (showAddForm = true)}
            >
              <UserPlus class="h-5 w-5" />
              Thêm phụ huynh đầu tiên
            </button>
          </div>
        {:else if filteredParents.length === 0}
          <!-- No search results -->
          <div class="flex flex-col items-center justify-center py-16 px-4">
            <div class="rounded-full bg-warning/10 p-6 mb-4">
              <Search class="h-12 w-12 text-warning" />
            </div>
            <h3 class="text-xl font-bold text-base-content/70 mb-2">
              Không tìm thấy kết quả
            </h3>
            <p class="text-base-content/50 text-center max-w-md mb-6">
              Không có phụ huynh nào khớp với từ khóa tìm kiếm của bạn.
            </p>
            <button
              class="btn btn-outline gap-2"
              onclick={() => (searchQuery = "")}
            >
              <X class="h-4 w-4" />
              Xóa tìm kiếm
            </button>
          </div>
        {:else}
          <!-- Parent Table -->
          <div class="overflow-x-auto">
            <table class="table">
              <thead>
                <tr class="bg-base-200/50">
                  <th class="font-semibold">Phụ huynh</th>
                  <th class="font-semibold">Thông tin liên hệ</th>
                  <th class="font-semibold">Học sinh liên kết</th>
                  <th class="font-semibold text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {#each filteredParents as parent (parent.id)}
                  <tr class="hover:bg-base-200/30 transition-colors">
                    <td>
                      <div class="flex items-center gap-3">
                        <div class="avatar placeholder">
                          <div
                            class="w-10 h-10 rounded-full bg-primary text-primary-content flex items-center justify-center"
                          >
                            <span class="text-sm font-bold">
                              {getInitials(parent.first_name, parent.last_name)}
                            </span>
                          </div>
                        </div>
                        <div>
                          <div class="font-semibold">
                            {parent.first_name}
                            {parent.last_name}
                          </div>
                          <div class="text-xs text-base-content/50">
                            @{parent.username}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div class="flex items-center gap-2 text-sm">
                        <Mail class="h-4 w-4 text-base-content/40 z-10" />
                        <span class="text-base-content/70">{parent.email}</span>
                      </div>
                    </td>
                    <td>
                      <div class="flex flex-wrap items-center gap-2">
                        {#each getLinkedStudents(parent.id) as link}
                          <div class="badge badge-outline gap-1.5 py-2.5 px-3">
                            <div class="avatar placeholder">
                              <div
                                class="w-4 h-4 rounded-full bg-secondary text-secondary-content flex items-center justify-center"
                              >
                                <span class="text-[8px]"
                                  >{link.first_name?.[0] ||
                                    link.student_id?.[0] ||
                                    "?"}</span
                                >
                              </div>
                            </div>
                            <span class="font-medium text-xs">
                              {link.first_name || ""}
                              {link.last_name || ""}
                            </span>
                          </div>
                        {/each}
                        <button
                          class="btn btn-xs btn-ghost btn-circle border border-dashed border-base-content/30 tooltip"
                          data-tip="Liên kết học sinh"
                          onclick={() => openLinkModal(parent)}
                        >
                          <Link2 class="h-3 w-3" />
                        </button>
                      </div>
                    </td>
                    <td>
                      <div class="flex justify-end gap-1">
                        <button
                          class="btn btn-sm btn-ghost hover:bg-primary/10 hover:text-primary tooltip"
                          data-tip="Chỉnh sửa"
                          onclick={() => openEditModal(parent)}
                        >
                          <Pencil class="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>

          <!-- Table Footer -->
          <div class="px-6 py-4 border-t border-base-200 bg-base-200/30">
            <p class="text-sm text-base-content/60">
              Hiển thị <span class="font-semibold"
                >{filteredParents.length}</span
              >
              trong tổng số
              <span class="font-semibold">{data.parents.length}</span> phụ huynh
            </p>
          </div>
        {/if}
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
          class="h-5 w-5 text-primary z-10"
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
      Sửa thông tin phụ huynh
    </h3>
    <p class="text-sm text-base-content/60 mb-4">
      Cập nhật thông tin tài khoản phụ huynh
    </p>

    {#if editingParent}
      <form
        class="space-y-4"
        method="POST"
        action="?/updateParent"
        use:enhance={createEnhance("update", "Cập nhật thành công!", () =>
          editDialog?.close(),
        )}
      >
        <input type="hidden" name="id" value={editingParent.id} />

        <div class="form-control">
          <label for="edit_email" class="label">
            <span class="label-text font-medium">Địa chỉ Email</span>
          </label>
          <div class="relative">
            <span
              class="absolute inset-y-0 left-0 flex items-center pl-3 text-base-content/40 z-10"
            >
              <svg
                class="h-5 w-5 z-10"
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
            <span class="label-text font-medium">Tên đăng nhập</span>
          </label>
          <div class="relative">
            <span
              class="absolute inset-y-0 left-0 flex items-center pl-3 text-base-content/40 z-10"
            >
              <svg
                class="h-5 w-5 z-10"
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
              <span class="label-text font-medium">Họ</span>
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
              <span class="label-text font-medium">Tên</span>
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

        <div class="divider my-2 text-xs">Đổi mật khẩu (Tùy chọn)</div>

        <div class="form-control">
          <label for="edit_password" class="label">
            <span class="label-text font-medium">Mật khẩu mới</span>
          </label>
          <div class="relative">
            <span
              class="absolute inset-y-0 left-0 flex items-center pl-3 text-base-content/40 z-10"
            >
              <svg
                class="h-5 w-5 z-10"
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
              placeholder="Để trống nếu không đổi"
              autocomplete="new-password"
              minlength="8"
              disabled={isLoading("update")}
            />
          </div>
          <div class="mt-1 text-xs text-base-content/60 pl-1">
            Chỉ điền nếu bạn muốn đổi mật khẩu
          </div>
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
                class="h-4 w-4 z-10"
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

<!-- Link Student Modal -->
<dialog bind:this={linkDialog} class="modal">
  <div class="modal-box w-11/12 max-w-2xl">
    <h3 class="font-bold text-xl mb-4">Liên kết học sinh với phụ huynh</h3>

    {#if linkingParent}
      <form
        method="POST"
        action="?/linkStudent"
        use:enhance={createEnhance("link", "Liên kết thành công!", () =>
          linkDialog?.close(),
        )}
        class="space-y-4"
      >
        <input type="hidden" name="parentId" value={linkingParent.id} />

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- 1. Select Class -->
          <div class="form-control">
            <label for="classSelect" class="label">
              <span class="label-text font-medium">1. Chọn lớp</span>
            </label>
            <select
              id="classSelect"
              class="select select-bordered w-full"
              bind:value={selectedClassId}
              disabled={isLoading("link")}
            >
              <option value={null} disabled selected>Chọn lớp...</option>
              {#each data.classes as cls}
                <option value={cls.id}>{cls.name}</option>
              {/each}
            </select>
          </div>

          <!-- 2. Select Student -->
          <div class="form-control">
            <label for="studentSelect" class="label">
              <span class="label-text font-medium">2. Chọn học sinh</span>
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
                {!selectedClassId ? "Chọn lớp trước" : "Chọn học sinh..."}
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
          HOẶC NHẬP THỦ CÔNG
        </div>

        <div class="form-control">
          <label for="manualStudentId" class="label">
            <span class="label-text font-medium">Mã học sinh (Nhập tay)</span>
          </label>
          <input
            type="text"
            name="studentId"
            id="manualStudentId"
            class="input input-bordered w-full font-mono"
            placeholder="Nhập mã nếu biết"
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
            Hủy
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            disabled={isLoading("link") || !selectedStudentId}
          >
            {#if isLoading("link")}
              <span class="loading loading-spinner loading-sm"></span>
              Đang liên kết...
            {:else}
              Liên kết
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
