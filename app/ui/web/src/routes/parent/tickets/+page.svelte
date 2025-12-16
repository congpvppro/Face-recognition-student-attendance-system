<script lang="ts">
  import { enhance } from "$app/forms";
  import { showToast } from "$lib/toastStore";
  import {
    FileText,
    Send,
    Calendar,
    User,
    Tag,
    MessageSquare,
    CheckCircle,
    XCircle,
    AlertTriangle,
  } from "lucide-svelte";

  type Student = {
    id: string;
    first_name: string;
    last_name: string;
    class_id: number;
    class_name: string;
  };

  type Ticket = {
    id: number;
    student_first_name: string;
    student_last_name: string;
    class_name: string;
    type: string;
    status: "pending" | "approved" | "rejected";
    reason: string;
    created_at: string;
    teacher_first_name: string | null;
    teacher_last_name: string | null;
  };

  let { data }: { data: { students: Student[]; tickets: Ticket[] } } = $props();

  let submitting = $state(false);
  let selectedStudentId = $state<string | null>(null);
  let selectedStudent = $derived(
    data.students.find((s) => s.id === selectedStudentId),
  );

  const statusMap = {
    pending: { text: "Chờ duyệt", color: "badge-warning", icon: AlertTriangle },
    approved: { text: "Đã duyệt", color: "badge-success", icon: CheckCircle },
    rejected: { text: "Từ chối", color: "badge-error", icon: XCircle },
  };
</script>

<svelte:head>
  <title>Gửi Đơn Xin Phép - Attendde</title>
</svelte:head>

<div class="container mx-auto p-4 md:p-8 max-w-6xl">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold flex items-center gap-3">
      <div class="rounded-lg bg-primary p-2">
        <FileText class="h-8 w-8 text-primary-content" />
      </div>
      Quản lý Đơn Xin Phép
    </h1>
    <p class="text-base-content/70 mt-2">
      Tạo và theo dõi các đơn xin nghỉ phép, đi muộn cho con của bạn.
    </p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <!-- Create Ticket Form -->
    <div class="lg:col-span-1">
      <div
        class="card bg-base-100 shadow-xl border border-base-300 sticky top-24"
      >
        <div class="card-body">
          <h2 class="card-title text-xl">
            <Send class="h-5 w-5" />
            Tạo Đơn Mới
          </h2>
          <div class="divider my-2"></div>

          <form
            method="POST"
            action="?/createTicket"
            class="space-y-4"
            use:enhance={() => {
              submitting = true;
              return async ({ result, update }) => {
                submitting = false;
                if (result.type === "success") {
                  showToast({
                    message: "Gửi đơn thành công!",
                    type: "success",
                  });
                  await update({ reset: true });
                } else if (result.type === "failure") {
                  showToast({
                    message: result.data?.message || "Gửi đơn thất bại.",
                    type: "error",
                  });
                }
              };
            }}
          >
            <div class="form-control">
              <label for="student_id" class="label font-medium"
                >Chọn học sinh</label
              >
              <select
                id="student_id"
                name="student_id"
                class="select select-bordered"
                required
                bind:value={selectedStudentId}
              >
                <option disabled selected value={null}>-- Chọn con --</option>
                {#each data.students as student}
                  <option value={student.id}
                    >{student.first_name}
                    {student.last_name} - Lớp {student.class_name}</option
                  >
                {/each}
              </select>
              {#if selectedStudent}
                <input
                  type="hidden"
                  name="class_id"
                  value={selectedStudent.class_id}
                />
              {/if}
            </div>

            <div class="form-control">
              <label for="type" class="label font-medium">Loại đơn</label>
              <select
                id="type"
                name="type"
                class="select select-bordered"
                required
              >
                <option value="leave">Xin nghỉ phép</option>
                <option value="late">Xin đi muộn</option>
                <option value="other">Khác</option>
              </select>
            </div>

            <div class="form-control">
              <label for="reason" class="label font-medium">Lý do</label>
              <textarea
                id="reason"
                name="reason"
                class="textarea textarea-bordered h-28"
                placeholder="Vui lòng trình bày rõ lý do..."
                required
              ></textarea>
            </div>

            <button
              type="submit"
              class="btn btn-primary w-full mt-6"
              disabled={submitting || !selectedStudent}
            >
              {#if submitting}
                <span class="loading loading-spinner"></span> Đang gửi...
              {:else}
                <Send class="h-4 w-4" /> Gửi Đơn
              {/if}
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Ticket List -->
    <div class="lg:col-span-2">
      <h2 class="text-2xl font-bold mb-4">Lịch sử đơn đã gửi</h2>
      {#if data.tickets.length === 0}
        <div class="alert">
          <FileText class="h-6 w-6" />
          <span>Bạn chưa gửi đơn nào.</span>
        </div>
      {:else}
        <div class="space-y-4">
          {#each data.tickets as ticket}
            <div class="card bg-base-100 shadow-md border border-base-200">
              <div class="card-body p-5">
                <div class="flex justify-between items-start">
                  <div>
                    <div class="flex items-center gap-2">
                      <div
                        class="badge {statusMap[ticket.status]
                          .color} badge-lg gap-2"
                      >
                        <svelte:component
                          this={statusMap[ticket.status].icon}
                          class="h-3 w-3"
                        />
                        {statusMap[ticket.status].text}
                      </div>
                      <div class="badge badge-outline">
                        {ticket.type === "leave"
                          ? "Nghỉ phép"
                          : ticket.type === "late"
                            ? "Đi muộn"
                            : "Khác"}
                      </div>
                    </div>
                    <p class="mt-3 text-base-content/80">{ticket.reason}</p>
                  </div>
                  <div class="text-right text-xs text-base-content/60">
                    {new Date(ticket.created_at).toLocaleString("vi-VN")}
                  </div>
                </div>

                <div class="divider my-3"></div>

                <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm">
                  <div class="flex items-center gap-2" title="Học sinh">
                    <User class="h-4 w-4 text-primary" />
                    <span class="font-medium"
                      >{ticket.student_first_name}
                      {ticket.student_last_name}</span
                    >
                  </div>
                  <div class="flex items-center gap-2" title="Lớp">
                    <Tag class="h-4 w-4 text-primary" />
                    <span>{ticket.class_name}</span>
                  </div>
                  <div class="flex items-center gap-2" title="Giáo viên xử lý">
                    <User class="h-4 w-4 text-secondary" />
                    <span
                      >{ticket.teacher_first_name
                        ? `${ticket.teacher_first_name} ${ticket.teacher_last_name}`
                        : "N/A"}</span
                    >
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
