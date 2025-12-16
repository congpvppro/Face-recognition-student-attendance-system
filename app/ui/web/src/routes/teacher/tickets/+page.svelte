<script lang="ts">
  import { enhance } from "$app/forms";
  import { showToast } from "$lib/toastStore";
  import { FileText, User, Tag, Clock, Check, X } from "lucide-svelte";

  type Ticket = {
    id: number;
    student_first_name: string;
    student_last_name: string;
    parent_first_name: string;
    parent_last_name: string;
    class_name: string;
    type: string;
    status: "pending" | "approved" | "rejected";
    reason: string;
    created_at: string;
  };

  let { data }: { data: { tickets: Ticket[] } } = $props();

  const statusMap = {
    pending: {
      text: "Chờ duyệt",
      color: "bg-yellow-100 text-yellow-800 border-yellow-300",
    },
    approved: {
      text: "Đã duyệt",
      color: "bg-green-100 text-green-800 border-green-300",
    },
    rejected: {
      text: "Từ chối",
      color: "bg-red-100 text-red-800 border-red-300",
    },
  };
</script>

<svelte:head>
  <title>Duyệt Đơn Xin Phép - Attendde</title>
</svelte:head>

<div class="container mx-auto p-4 md:p-8 max-w-7xl">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold flex items-center gap-3">
      <div class="rounded-lg bg-secondary p-2">
        <FileText class="h-8 w-8 text-secondary-content" />
      </div>
      Duyệt Đơn Xin Phép
    </h1>
    <p class="text-base-content/70 mt-2">
      Xem và xử lý các đơn xin phép từ phụ huynh cho các lớp bạn chủ nhiệm.
    </p>
  </div>

  {#if data.tickets.length === 0}
    <div class="alert shadow-lg">
      <FileText class="h-6 w-6" />
      <span>Không có đơn xin phép nào cần xử lý.</span>
    </div>
  {:else}
    <div class="overflow-x-auto">
      <table class="table table-zebra w-full">
        <thead class="bg-base-200">
          <tr>
            <th class="w-1/4">Học sinh & Lớp</th>
            <th>Phụ huynh</th>
            <th class="w-1/3">Lý do</th>
            <th>Loại đơn</th>
            <th>Trạng thái & Hành động</th>
          </tr>
        </thead>
        <tbody>
          {#each data.tickets as ticket (ticket.id)}
            <tr class="hover">
              <td>
                <div class="font-bold">
                  {ticket.student_first_name}
                  {ticket.student_last_name}
                </div>
                <div class="text-sm opacity-50">{ticket.class_name}</div>
              </td>
              <td>
                {ticket.parent_first_name}
                {ticket.parent_last_name}
              </td>
              <td class="whitespace-normal">
                <p class="max-w-md">{ticket.reason}</p>
                <div class="text-xs opacity-60 mt-1 flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  {new Date(ticket.created_at).toLocaleString("vi-VN")}
                </div>
              </td>
              <td>
                <span class="badge badge-ghost">
                  {ticket.type === "leave"
                    ? "Nghỉ phép"
                    : ticket.type === "late"
                      ? "Đi muộn"
                      : "Khác"}
                </span>
              </td>
              <td>
                <div class="flex items-center gap-2">
                  <div
                    class="badge {statusMap[ticket.status].color} p-3 font-bold"
                  >
                    {statusMap[ticket.status].text}
                  </div>
                  {#if ticket.status === "pending"}
                    <form
                      method="POST"
                      action="?/updateStatus"
                      use:enhance={() => {
                        return async ({ result, update }) => {
                          if (result.type === "success") {
                            showToast({
                              message: result.data?.message,
                              type: "success",
                            });
                            await update();
                          } else if (result.type === "failure") {
                            showToast({
                              message: result.data?.message,
                              type: "error",
                            });
                          }
                        };
                      }}
                      class="flex gap-1"
                    >
                      <input type="hidden" name="ticketId" value={ticket.id} />
                      <button
                        type="submit"
                        name="status"
                        value="approved"
                        class="btn btn-xs btn-success btn-outline btn-circle"
                        title="Duyệt"
                      >
                        <Check class="h-4 w-4" />
                      </button>
                      <button
                        type="submit"
                        name="status"
                        value="rejected"
                        class="btn btn-xs btn-error btn-outline btn-circle"
                        title="Từ chối"
                      >
                        <X class="h-4 w-4" />
                      </button>
                    </form>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
