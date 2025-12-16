<script lang="ts">
  import {
    BarChart3,
    Users,
    Filter,
    Calendar,
    School,
    TrendingUp,
    Clock,
    UserX,
    CheckCircle2,
    AlertCircle,
  } from "lucide-svelte";
  import { goto } from "$app/navigation";
  import type { PageData } from "./$types";

  // Total sessions per day (matching Python DB class_schedule)
  const TOTAL_SESSIONS = 5;

  let { data }: { data: PageData } = $props();

  // Local state for form controls
  let selectedClassIdLocal = $state(data.selectedClassId);
  let selectedDateLocal = $state(data.selectedDate);

  // Update local state when data changes
  $effect(() => {
    selectedClassIdLocal = data.selectedClassId;
    selectedDateLocal = data.selectedDate;
  });

  // Function to handle filter changes and reload the page with new query params
  const applyFilters = () => {
    if (selectedClassIdLocal) {
      const url = new URL(window.location.href);
      url.searchParams.set("classId", selectedClassIdLocal.toString());
      url.searchParams.set("date", selectedDateLocal);
      goto(url.toString(), {
        invalidateAll: true,
      });
    }
  };

  // Calculate statistics for the selected class
  const studentStats = $derived.by(() => {
    if (!data.students || data.students.length === 0) return [];

    const attendanceByStudent = data.attendance.reduce(
      (acc, record) => {
        const studentId = record.student_id;
        if (!acc[studentId]) {
          acc[studentId] = [];
        }
        acc[studentId].push(record);
        return acc;
      },
      {} as Record<string, any[]>,
    );

    return data.students.map((student) => {
      const records = attendanceByStudent[student.id] || [];
      const present = records.filter(
        (r) =>
          r.attendance_status === "on_time" ||
          r.attendance_status === "present",
      ).length;
      const late = records.filter((r) => r.attendance_status === "late").length;
      const excused = records.filter(
        (r) => r.attendance_status === "excused",
      ).length;
      const totalAttended = present + late + excused;
      const absent = Math.max(0, TOTAL_SESSIONS - totalAttended);

      return {
        ...student,
        present,
        late,
        excused,
        absent,
        rate:
          TOTAL_SESSIONS > 0
            ? Math.round((totalAttended / TOTAL_SESSIONS) * 100)
            : 0,
      };
    });
  });

  const overallAttendanceRate = $derived.by(() => {
    if (studentStats.length === 0) return 0;
    const totalRate = studentStats.reduce((sum, s) => sum + s.rate, 0);
    const avgRate = totalRate / studentStats.length;
    return isNaN(avgRate) ? 0 : Math.round(avgRate);
  });

  const totalPresentSessions = $derived(
    studentStats.reduce((sum, s) => sum + s.present, 0),
  );
  const totalLateSessions = $derived(
    studentStats.reduce((sum, s) => sum + s.late, 0),
  );
  const totalAbsentSessions = $derived(
    studentStats.reduce((sum, s) => sum + s.absent, 0),
  );

  // Get attendance rate color
  function getRateColor(rate: number): string {
    if (rate >= 80) return "text-success";
    if (rate >= 60) return "text-warning";
    return "text-error";
  }

  function getRateBgColor(rate: number): string {
    if (rate >= 80) return "bg-success";
    if (rate >= 60) return "bg-warning";
    return "bg-error";
  }

  // Get initials for avatar
  function getInitials(firstName: string, lastName: string): string {
    return `${firstName[0] || ""}${lastName[0] || ""}`.toUpperCase();
  }

  // Format date for display
  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString("vi-VN", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  // Get selected class name
  let selectedClassName = $derived(
    data.classes.find((c) => c.id === data.selectedClassId)?.name || "",
  );
</script>

<svelte:head>
  <title>Thống kê chuyên cần - Attendde</title>
</svelte:head>

<div class="min-h-screen bg-base-200/50">
  <div class="container mx-auto p-4 md:p-8 max-w-7xl">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold flex items-center gap-3">
        <div class="rounded-xl bg-primary p-2.5 shadow-lg">
          <BarChart3 class="h-7 w-7 text-primary-content" />
        </div>
        Thống kê chuyên cần
      </h1>
      <p class="text-base-content/60 mt-2">
        Xem và phân tích dữ liệu điểm danh theo lớp và ngày
      </p>
    </div>

    <!-- Filter Controls -->
    <div class="card bg-base-100 shadow-md mb-8">
      <div class="card-body p-4 md:p-6">
        <div class="flex flex-col lg:flex-row gap-4 items-end">
          <div class="form-control flex-1 w-full">
            <label class="label">
              <span class="label-text font-medium flex items-center gap-2">
                <School class="h-4 w-4" />
                Chọn lớp
              </span>
            </label>
            <select
              bind:value={selectedClassIdLocal}
              class="select select-bordered w-full"
            >
              <option value={null} disabled>-- Chọn lớp học --</option>
              {#each data.classes as cls}
                <option value={cls.id}>{cls.name}</option>
              {/each}
            </select>
          </div>

          <div class="form-control flex-1 w-full">
            <label class="label">
              <span class="label-text font-medium flex items-center gap-2">
                <Calendar class="h-4 w-4" />
                Chọn ngày
              </span>
            </label>
            <input
              type="date"
              bind:value={selectedDateLocal}
              class="input input-bordered w-full"
            />
          </div>

          <button
            class="btn btn-primary gap-2 w-full lg:w-auto min-w-[140px]"
            onclick={applyFilters}
            disabled={!selectedClassIdLocal}
          >
            <Filter class="w-4 h-4" />
            Xem báo cáo
          </button>
        </div>
      </div>
    </div>

    {#if data.selectedClassId}
      <!-- Report Header -->
      <div
        class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6"
      >
        <div>
          <h2 class="text-xl font-bold flex items-center gap-2">
            <School class="h-5 w-5 text-primary" />
            {selectedClassName}
          </h2>
          <p class="text-base-content/60 text-sm mt-1">
            {formatDate(data.selectedDate)}
          </p>
        </div>
        {#if data.students.length > 0}
          <div class="badge badge-lg gap-2 py-3 px-4">
            <Users class="h-4 w-4" />
            Sĩ số: {data.students.length} học sinh
          </div>
        {/if}
      </div>

      <!-- Stats Cards -->
      {#if data.students.length > 0}
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div class="card bg-base-100 shadow-md">
            <div class="card-body p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p
                    class="text-xs text-base-content/60 font-medium uppercase tracking-wide"
                  >
                    Tỉ lệ chuyên cần
                  </p>
                  <p
                    class="text-3xl font-bold mt-1 {getRateColor(
                      overallAttendanceRate,
                    )}"
                  >
                    {overallAttendanceRate}%
                  </p>
                </div>
                <div class="rounded-xl bg-primary/10 p-3">
                  <TrendingUp class="h-6 w-6 text-primary" />
                </div>
              </div>
              <!-- Progress bar -->
              <div class="w-full bg-base-200 rounded-full h-2 mt-3">
                <div
                  class="h-2 rounded-full transition-all duration-500 {getRateBgColor(
                    overallAttendanceRate,
                  )}"
                  style="width: {overallAttendanceRate}%"
                ></div>
              </div>
            </div>
          </div>

          <div class="card bg-base-100 shadow-md">
            <div class="card-body p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p
                    class="text-xs text-base-content/60 font-medium uppercase tracking-wide"
                  >
                    Có mặt
                  </p>
                  <p class="text-3xl font-bold text-success mt-1">
                    {totalPresentSessions}
                  </p>
                </div>
                <div class="rounded-xl bg-success/10 p-3">
                  <CheckCircle2 class="h-6 w-6 text-success" />
                </div>
              </div>
              <p class="text-xs text-base-content/50 mt-2">lượt điểm danh</p>
            </div>
          </div>

          <div class="card bg-base-100 shadow-md">
            <div class="card-body p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p
                    class="text-xs text-base-content/60 font-medium uppercase tracking-wide"
                  >
                    Đi muộn
                  </p>
                  <p class="text-3xl font-bold text-warning mt-1">
                    {totalLateSessions}
                  </p>
                </div>
                <div class="rounded-xl bg-warning/10 p-3">
                  <Clock class="h-6 w-6 text-warning" />
                </div>
              </div>
              <p class="text-xs text-base-content/50 mt-2">lượt đi muộn</p>
            </div>
          </div>

          <div class="card bg-base-100 shadow-md">
            <div class="card-body p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p
                    class="text-xs text-base-content/60 font-medium uppercase tracking-wide"
                  >
                    Vắng mặt
                  </p>
                  <p class="text-3xl font-bold text-error mt-1">
                    {totalAbsentSessions}
                  </p>
                </div>
                <div class="rounded-xl bg-error/10 p-3">
                  <UserX class="h-6 w-6 text-error" />
                </div>
              </div>
              <p class="text-xs text-base-content/50 mt-2">lượt vắng</p>
            </div>
          </div>
        </div>
      {/if}

      <!-- Student Statistics Table -->
      <div class="card bg-base-100 shadow-lg">
        <div class="card-body p-0">
          {#if data.students.length > 0}
            <div class="overflow-x-auto">
              <table class="table">
                <thead>
                  <tr class="bg-base-200/50">
                    <th class="font-semibold">Học sinh</th>
                    <th class="font-semibold text-center">Có mặt</th>
                    <th class="font-semibold text-center">Đi muộn</th>
                    <th class="font-semibold text-center">Vắng</th>
                    <th class="font-semibold text-center">Tỉ lệ chuyên cần</th>
                  </tr>
                </thead>
                <tbody>
                  {#each studentStats as stat (stat.id)}
                    <tr class="hover:bg-base-200/30 transition-colors">
                      <td>
                        <div class="flex items-center gap-3">
                          <div class="avatar placeholder">
                            <div
                              class="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold"
                            >
                              <span class="text-sm font-bold">
                                {getInitials(stat.first_name, stat.last_name)}
                              </span>
                            </div>
                          </div>
                          <div>
                            <div class="font-semibold">
                              {stat.first_name}
                              {stat.last_name}
                            </div>
                            <code
                              class="text-xs bg-base-200 px-2 py-0.5 rounded font-mono"
                            >
                              {stat.id}
                            </code>
                          </div>
                        </div>
                      </td>
                      <td class="text-center">
                        <span
                          class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-success/10 text-success font-bold text-sm"
                        >
                          {stat.present}
                        </span>
                      </td>
                      <td class="text-center">
                        <span
                          class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-warning/10 text-warning font-bold text-sm"
                        >
                          {stat.late}
                        </span>
                      </td>
                      <td class="text-center">
                        <span
                          class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-error/10 text-error font-bold text-sm"
                        >
                          {stat.absent}
                        </span>
                      </td>
                      <td class="text-center">
                        <div class="flex items-center justify-center gap-3">
                          <div class="w-24 bg-base-200 rounded-full h-2.5">
                            <div
                              class="h-2.5 rounded-full transition-all duration-300 {getRateBgColor(
                                stat.rate,
                              )}"
                              style="width: {stat.rate}%"
                            ></div>
                          </div>
                          <span
                            class="font-bold text-sm w-12 {getRateColor(
                              stat.rate,
                            )}"
                          >
                            {stat.rate}%
                          </span>
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
                Tổng cộng <span class="font-semibold"
                  >{data.students.length}</span
                >
                học sinh · <span class="font-semibold">{TOTAL_SESSIONS}</span> tiết
                học/ngày
              </p>
            </div>
          {:else}
            <!-- Empty state for class with no students -->
            <div class="flex flex-col items-center justify-center py-16 px-4">
              <div class="rounded-full bg-warning/10 p-6 mb-4">
                <AlertCircle class="h-12 w-12 text-warning" />
              </div>
              <h3 class="text-xl font-bold text-base-content/70 mb-2">
                Không có học sinh
              </h3>
              <p class="text-base-content/50 text-center max-w-md">
                Lớp học này chưa có học sinh nào. Vui lòng thêm học sinh vào lớp
                để xem thống kê điểm danh.
              </p>
            </div>
          {/if}
        </div>
      </div>
    {:else}
      <!-- No class selected state -->
      <div class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <div class="flex flex-col items-center justify-center py-16 px-4">
            <div class="rounded-full bg-base-200 p-6 mb-4">
              <BarChart3 class="h-12 w-12 text-base-content/30" />
            </div>
            <h3 class="text-xl font-bold text-base-content/70 mb-2">
              Chọn lớp để xem thống kê
            </h3>
            <p class="text-base-content/50 text-center max-w-md mb-6">
              Vui lòng chọn một lớp học và ngày từ bộ lọc phía trên để xem báo
              cáo điểm danh chi tiết.
            </p>
            <div class="flex items-center gap-4 text-sm text-base-content/40">
              <div class="flex items-center gap-2">
                <CheckCircle2 class="h-4 w-4 text-success" />
                <span>Có mặt</span>
              </div>
              <div class="flex items-center gap-2">
                <Clock class="h-4 w-4 text-warning" />
                <span>Đi muộn</span>
              </div>
              <div class="flex items-center gap-2">
                <UserX class="h-4 w-4 text-error" />
                <span>Vắng mặt</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>
