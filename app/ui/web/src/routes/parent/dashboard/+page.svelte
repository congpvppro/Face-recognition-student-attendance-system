<script lang="ts">
  import { AlertCircle, CheckCircle2, Clock, Calendar } from "lucide-svelte";
  import type { PageData } from "./$types";

  // Total sessions per day (matching Python DB class_schedule)
  const TOTAL_SESSIONS = 5;

  let { data }: { data: PageData } = $props();

  // Helper to group attendance records by date for easier display
  const groupAttendanceByDate = (attendance: any[]) => {
    if (!attendance) return {};
    return attendance.reduce(
      (acc, record) => {
        const date = record.session_date;
        if (!acc[date]) {
          acc[date] = [];
        }
        acc[date].push(record);
        return acc;
      },
      {} as Record<string, any[]>,
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("vi-VN", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const getStatusInfo = (status: string | undefined) => {
    switch (status) {
      case "present":
      case "on_time":
        return {
          label: "Có mặt",
          icon: CheckCircle2,
          color: "text-success",
          bgColor: "bg-success/10",
        };
      case "late":
        return {
          label: "Đi muộn",
          icon: Clock,
          color: "text-warning",
          bgColor: "bg-warning/10",
        };
      case "absent":
        return {
          label: "Vắng mặt",
          icon: AlertCircle,
          color: "text-error",
          bgColor: "bg-error/10",
        };
      case "excused":
        return {
          label: "Có phép",
          icon: CheckCircle2,
          color: "text-info",
          bgColor: "bg-info/10",
        };
      case "left_early":
        return {
          label: "Về sớm",
          icon: Clock,
          color: "text-warning",
          bgColor: "bg-warning/10",
        };
      default:
        return {
          label: "Vắng mặt",
          icon: AlertCircle,
          color: "text-error",
          bgColor: "bg-error/10",
        };
    }
  };
</script>

<div class="container mx-auto p-6 max-w-5xl">
  <div class="mb-8">
    <h1 class="text-3xl font-bold font-montserrat text-gray-900">
      Bảng theo dõi điểm danh
    </h1>
    <p class="text-gray-600 mt-1">
      Xem chi tiết lịch sử điểm danh theo từng ngày và từng tiết học của con em
      bạn.
    </p>
  </div>

  {#if !data.students || data.students.length === 0}
    <div class="alert">
      <AlertCircle class="w-6 h-6" />
      <span>Chưa có thông tin học sinh được liên kết với tài khoản này.</span>
    </div>
  {:else}
    <div class="space-y-10">
      {#each data.students as student}
        {@const attendanceByDate = groupAttendanceByDate(student.attendance)}
        {@const sortedDates = Object.keys(attendanceByDate).sort(
          (a, b) => new Date(b).getTime() - new Date(a).getTime(),
        )}

        <div class="bg-white rounded-2xl shadow-sm border border-gray-200">
          <!-- Student Header -->
          <div class="p-6 flex items-center gap-4">
            <div class="avatar placeholder">
              <div
                class="bg-primary text-primary-content rounded-full w-12 flex items-center justify-center"
              >
                <span class="text-xl font-bold">{student.first_name[0]}</span>
              </div>
            </div>
            <div>
              <h2 class="text-xl font-bold text-gray-900">
                {student.first_name}
                {student.last_name}
              </h2>
              <p class="text-sm text-gray-500 font-mono">ID: {student.id}</p>
            </div>
          </div>

          <!-- Attendance History -->
          <div class="p-6 space-y-6">
            {#if sortedDates.length === 0}
              <div class="py-12 text-center text-gray-500">
                <Calendar class="w-12 h-12 mx-auto mb-2 opacity-50" />
                Chưa có dữ liệu điểm danh nào được ghi nhận.
              </div>
            {:else}
              {#each sortedDates as date}
                {@const recordsForDay = attendanceByDate[date]}
                <div class="bg-base-100 p-4 rounded-lg border">
                  <h3 class="font-bold text-base mb-3">{formatDate(date)}</h3>
                  <div
                    class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3"
                  >
                    <!-- Display all sessions -->
                    {#each { length: TOTAL_SESSIONS } as _, i}
                      {@const sessionNumber = i + 1}
                      {@const record = recordsForDay.find(
                        (r: any) => r.session_number === sessionNumber,
                      )}
                      {@const status = getStatusInfo(record?.attendance_status)}

                      <div class={`p-3 rounded-lg border ${status.bgColor}`}>
                        <p class="text-xs font-bold text-gray-500 mb-1.5">
                          Tiết {sessionNumber}
                        </p>
                        <div
                          class={`flex items-center gap-1.5 text-sm font-semibold ${status.color}`}
                        >
                          {#if status.icon}
                            <svelte:component
                              this={status.icon}
                              class="w-4 h-4"
                            />
                          {/if}
                          <span>{status.label}</span>
                        </div>
                        {#if record && record.entry_time}
                          <p class="text-xs text-gray-500 mt-1 font-mono">
                            {record.entry_time}
                          </p>
                        {/if}
                      </div>
                    {/each}
                  </div>
                </div>
              {/each}
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
