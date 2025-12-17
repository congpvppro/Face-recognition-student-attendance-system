<script lang="ts">
  import { enhance } from "$app/forms";
  import { invalidateAll, goto } from "$app/navigation";
  import { showToast } from "$lib/toastStore";
  import {
    Users,
    UserPlus,
    BarChart3,
    CheckCircle2,
    AlertCircle,
    Clock,
    Download,
    Search,
    ChevronLeft,
    ChevronRight,
    CalendarDays,
    X,
    ScanFace,
    Check,
    XCircle,
    FileCheck,
    ArrowLeft,
  } from "lucide-svelte";
  import type { PageData } from "./$types";

  // Total sessions per day (matching Python DB class_schedule)
  const TOTAL_SESSIONS = 5;

  // Student type matching unified database schema
  type Student = {
    id: string;
    name: string;
    first_name: string | null;
    last_name: string | null;
    face_registered: number | null;
  };

  type AttendanceRecord = {
    student_id: string;
    session_date: string;
    entry_time: string | null;
    exit_time: string | null;
    attendance_status: string;
    late_minutes: number;
    session_number: number;
  };

  let { data }: { data: PageData } = $props();

  let showAddModal = $state(false);
  let searchQuery = $state("");
  let selectedDate = $state(data.selectedDate);
  let isUpdating = $state(false);

  // Date navigation helpers
  function navigateDate(days: number) {
    const date = new Date(selectedDate);
    date.setDate(date.getDate() + days);
    onDateChange(date.toISOString().split("T")[0]);
  }

  function goToToday() {
    onDateChange(new Date().toISOString().split("T")[0]);
  }

  function onDateChange(newDate: string) {
    selectedDate = newDate;
    goto(`?date=${newDate}`, { invalidateAll: true });
  }

  function isToday(dateStr: string): boolean {
    return dateStr === new Date().toISOString().split("T")[0];
  }

  // Helper to get display name for student
  function getStudentDisplayName(student: Student): string {
    if (student.first_name && student.last_name) {
      return `${student.first_name} ${student.last_name}`;
    }
    return student.name || student.id;
  }

  // Get initials for avatar
  function getInitials(student: Student): string {
    if (student.first_name && student.last_name) {
      return `${student.first_name[0]}${student.last_name[0]}`.toUpperCase();
    }
    if (student.name) {
      const parts = student.name.split(" ");
      return parts.length >= 2
        ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
        : student.name[0].toUpperCase();
    }
    return student.id[0]?.toUpperCase() || "?";
  }

  // Filter students by search query
  const filteredStudents = $derived.by(() => {
    if (!searchQuery.trim()) return data.classDetail.students;
    const query = searchQuery.toLowerCase();
    return data.classDetail.students.filter((s: Student) => {
      const displayName = getStudentDisplayName(s).toLowerCase();
      return displayName.includes(query) || s.id.toLowerCase().includes(query);
    });
  });

  // Group all attendance records by student ID for efficient lookup
  const attendanceByStudent = $derived.by(() => {
    return data.attendance.reduce(
      (acc: Record<string, AttendanceRecord[]>, record: AttendanceRecord) => {
        const studentId = record.student_id;
        if (!acc[studentId]) {
          acc[studentId] = [];
        }
        acc[studentId].push(record);
        return acc;
      },
      {} as Record<string, AttendanceRecord[]>,
    );
  });

  // Calculate overall attendance stats
  const totalStudents = $derived(data.classDetail.students.length);

  const studentsPresentToday = $derived.by(() => {
    const presentStudentIds = new Set<string>();
    for (const record of data.attendance) {
      if (
        record.attendance_status === "on_time" ||
        record.attendance_status === "present"
      ) {
        presentStudentIds.add(record.student_id);
      }
    }
    return presentStudentIds.size;
  });

  const studentsLateToday = $derived.by(() => {
    const lateStudentIds = new Set<string>();
    for (const record of data.attendance) {
      if (record.attendance_status === "late") {
        lateStudentIds.add(record.student_id);
      }
    }
    return lateStudentIds.size;
  });

  const studentsAbsentToday = $derived.by(() => {
    const absentStudentIds = new Set<string>();
    const presentOrLateStudentIds = new Set<string>();

    for (const record of data.attendance) {
      if (record.attendance_status !== "absent") {
        presentOrLateStudentIds.add(record.student_id);
      }
    }

    for (const student of data.classDetail.students) {
      if (!presentOrLateStudentIds.has(student.id)) {
        absentStudentIds.add(student.id);
      }
    }

    return totalStudents - presentOrLateStudentIds.size;
  });

  const attendanceRate = $derived(
    totalStudents > 0
      ? Math.round(
          ((totalStudents - studentsAbsentToday) / totalStudents) * 100,
        )
      : 0,
  );

  // Session stats
  const sessionStats = $derived.by(() => {
    return Array.from({ length: TOTAL_SESSIONS }, (_, i) => {
      const sessionNum = i + 1;
      let present = 0;
      let late = 0;
      let absent = 0;
      let excused = 0;

      for (const student of data.classDetail.students) {
        const records = attendanceByStudent[student.id] || [];
        const record = records.find(
          (r: AttendanceRecord) => r.session_number === sessionNum,
        );
        const status = record?.attendance_status;

        if (status === "on_time" || status === "present") present++;
        else if (status === "late") late++;
        else if (status === "excused") excused++;
        else absent++;
      }

      return { present, late, absent, excused };
    });
  });

  const statusConfig = {
    on_time: {
      label: "Có mặt",
      shortLabel: "CM",
      icon: CheckCircle2,
      color: "text-success",
      bgColor: "bg-success/10",
      badgeClass: "badge-success",
    },
    present: {
      label: "Có mặt",
      shortLabel: "CM",
      icon: CheckCircle2,
      color: "text-success",
      bgColor: "bg-success/10",
      badgeClass: "badge-success",
    },
    late: {
      label: "Đi muộn",
      shortLabel: "ĐM",
      icon: Clock,
      color: "text-warning",
      bgColor: "bg-warning/10",
      badgeClass: "badge-warning",
    },
    absent: {
      label: "Vắng",
      shortLabel: "V",
      icon: XCircle,
      color: "text-error",
      bgColor: "bg-error/10",
      badgeClass: "badge-error",
    },
    excused: {
      label: "Có phép",
      shortLabel: "CP",
      icon: FileCheck,
      color: "text-info",
      bgColor: "bg-info/10",
      badgeClass: "badge-info",
    },
    left_early: {
      label: "Về sớm",
      shortLabel: "VS",
      icon: Clock,
      color: "text-warning",
      bgColor: "bg-warning/10",
      badgeClass: "badge-warning",
    },
  };

  const getStatusInfo = (status: string | undefined) => {
    if (!status || status === "absent") return statusConfig.absent;
    return (
      statusConfig[status as keyof typeof statusConfig] || statusConfig.absent
    );
  };

  // Export attendance data as CSV (daily by session)
  async function exportAttendance() {
    try {
      const classId = data.classDetail.id;
      const token =
        document.cookie
          .split("; ")
          .find((row) => row.startsWith("auth="))
          ?.split("=")[1] || "";

      const response = await fetch(
        `http://localhost:8000/api/attendance/export?class_id=${classId}&date=${selectedDate}`,
        {
          credentials: "include",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error("Failed to export attendance");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `attendance_${data.classDetail.name}_${selectedDate}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      showToast({ message: "Xuất file thành công!", type: "success" });
    } catch (error) {
      console.error("Export failed, using fallback:", error);
      // Fallback to client-side export
      const headers = [
        "Mã HS",
        "Họ tên",
        "Tiết 1",
        "Tiết 2",
        "Tiết 3",
        "Tiết 4",
        "Tiết 5",
      ];
      const rows = data.classDetail.students.map((student: Student) => {
        const records = attendanceByStudent[student.id] || [];
        const sessions = Array.from({ length: TOTAL_SESSIONS }, (_, i) => {
          const sessionNum = i + 1;
          const record = records.find(
            (r: AttendanceRecord) => r.session_number === sessionNum,
          );
          return record?.attendance_status || "absent";
        });
        return [student.id, getStudentDisplayName(student), ...sessions];
      });

      const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
      const blob = new Blob(["\ufeff" + csv], {
        type: "text/csv;charset=utf-8;",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `attendance_${data.classDetail.name}_${selectedDate}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      showToast({ message: "Xuất file thành công!", type: "success" });
    }
  }

  // Export student summary report (total attendance stats)
  async function exportStudentReport(includeDate: boolean = false) {
    try {
      const classId = data.classDetail.id;

      // Use TypeScript API which handles auth at SvelteKit level
      let url = `/api/attendance/export-report?classId=${classId}`;
      if (includeDate) {
        url += `&date=${selectedDate}`;
      }

      const response = await fetch(url, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Failed to export student report");
      }

      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      const suffix = includeDate ? `_${selectedDate}` : "_total";
      link.download = `student_report_${data.classDetail.name}${suffix}.csv`;
      link.click();
      URL.revokeObjectURL(downloadUrl);
      showToast({ message: "Xuất báo cáo thành công!", type: "success" });
    } catch (error) {
      console.error("Export student report failed:", error);
      showToast({ message: "Xuất báo cáo thất bại", type: "error" });
    }
  }

  function formatDateDisplay(dateStr: string): string {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (dateStr === today.toISOString().split("T")[0]) {
      return "Hôm nay";
    } else if (dateStr === yesterday.toISOString().split("T")[0]) {
      return "Hôm qua";
    }
    return date.toLocaleDateString("vi-VN", {
      weekday: "long",
      day: "numeric",
      month: "numeric",
    });
  }
</script>

<svelte:head>
  <title>{data.classDetail.name} - Điểm danh</title>
</svelte:head>

<div class="min-h-screen bg-base-200/50">
  <div class="container mx-auto p-4 md:p-6 max-w-7xl">
    <!-- Header -->
    <div class="mb-6">
      <!-- Breadcrumb -->
      <div class="flex items-center gap-2 text-sm mb-4">
        <a
          href="/teacher/classes"
          class="flex items-center gap-1 text-base-content/60 hover:text-primary transition-colors"
        >
          <ArrowLeft class="w-4 h-4" />
          Quay lại
        </a>
        <span class="text-base-content/40">/</span>
        <span class="text-base-content/80 font-medium"
          >{data.classDetail.name}</span
        >
      </div>

      <div
        class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4"
      >
        <div>
          <h1
            class="text-2xl md:text-3xl font-bold text-base-content flex items-center gap-3"
          >
            <div class="bg-primary/10 p-2.5 rounded-xl">
              <Users class="w-6 h-6 md:w-7 md:h-7 text-primary" />
            </div>
            {data.classDetail.name}
          </h1>
          <p class="text-base-content/60 mt-1 ml-14">
            {totalStudents} học sinh • Giáo viên: {data.classDetail.teacher ||
              "Chưa phân công"}
          </p>
        </div>
        <button
          class="btn btn-primary gap-2 shadow-md"
          onclick={() => (showAddModal = true)}
        >
          <UserPlus class="w-4 h-4" />
          Thêm học sinh
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">
      <div class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow">
        <div class="card-body p-4">
          <div class="flex items-center gap-3">
            <div class="bg-primary/10 p-2.5 rounded-xl">
              <Users class="text-primary w-5 h-5" />
            </div>
            <div>
              <p class="text-xs text-base-content/60 font-medium">Sĩ số</p>
              <p class="text-xl font-bold text-base-content">{totalStudents}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow">
        <div class="card-body p-4">
          <div class="flex items-center gap-3">
            <div class="bg-success/10 p-2.5 rounded-xl">
              <CheckCircle2 class="text-success w-5 h-5" />
            </div>
            <div>
              <p class="text-xs text-base-content/60 font-medium">Có mặt</p>
              <p class="text-xl font-bold text-success">
                {studentsPresentToday}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow">
        <div class="card-body p-4">
          <div class="flex items-center gap-3">
            <div class="bg-warning/10 p-2.5 rounded-xl">
              <Clock class="text-warning w-5 h-5" />
            </div>
            <div>
              <p class="text-xs text-base-content/60 font-medium">Đi muộn</p>
              <p class="text-xl font-bold text-warning">{studentsLateToday}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow">
        <div class="card-body p-4">
          <div class="flex items-center gap-3">
            <div class="bg-error/10 p-2.5 rounded-xl">
              <XCircle class="text-error w-5 h-5" />
            </div>
            <div>
              <p class="text-xs text-base-content/60 font-medium">Vắng</p>
              <p class="text-xl font-bold text-error">{studentsAbsentToday}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Attendance Table Card -->
    <div class="card bg-base-100 shadow-lg">
      <!-- Card Header with Date Navigation -->
      <div class="card-body p-4 md:p-6 pb-0">
        <div
          class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-4"
        >
          <!-- Date Navigation -->
          <div class="flex items-center gap-2 flex-wrap">
            <div class="join">
              <button
                class="btn btn-sm join-item"
                onclick={() => navigateDate(-1)}
                aria-label="Ngày trước"
              >
                <ChevronLeft class="w-4 h-4" />
              </button>
              <button
                class="btn btn-sm join-item min-w-[140px] font-medium"
                onclick={goToToday}
              >
                <CalendarDays class="w-4 h-4 mr-1" />
                {formatDateDisplay(selectedDate)}
              </button>
              <button
                class="btn btn-sm join-item"
                onclick={() => navigateDate(1)}
                aria-label="Ngày sau"
              >
                <ChevronRight class="w-4 h-4" />
              </button>
            </div>
            <input
              type="date"
              class="input input-sm input-bordered w-36"
              value={selectedDate}
              onchange={(e) => onDateChange(e.currentTarget.value)}
            />
            {#if !isToday(selectedDate)}
              <button class="btn btn-sm btn-ghost" onclick={goToToday}>
                Hôm nay
              </button>
            {/if}
          </div>

          <!-- Search and Actions -->
          <div class="flex items-center gap-2 flex-wrap">
            <div class="relative">
              <Search
                class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-base-content/40 z-10"
              />
              <input
                type="text"
                placeholder="Tìm học sinh..."
                class="input input-sm input-bordered pl-9 w-44"
                bind:value={searchQuery}
              />
              {#if searchQuery}
                <button
                  class="absolute right-2 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs btn-circle"
                  onclick={() => (searchQuery = "")}
                >
                  <X class="w-3 h-3" />
                </button>
              {/if}
            </div>
            <div class="dropdown dropdown-end">
              <button tabindex="0" class="btn btn-sm btn-outline gap-1">
                <Download class="w-4 h-4" />
                <span class="hidden sm:inline">Xuất báo cáo</span>
              </button>
              <ul
                tabindex="0"
                class="dropdown-content z-[1] menu p-2 shadow-lg bg-base-100 rounded-box w-56"
              >
                <li>
                  <button onclick={exportAttendance}>
                    <CalendarDays class="w-4 h-4" />
                    Điểm danh theo tiết ({formatDateDisplay(selectedDate)})
                  </button>
                </li>
                <li>
                  <button onclick={() => exportStudentReport(true)}>
                    <BarChart3 class="w-4 h-4" />
                    Thống kê ngày {formatDateDisplay(selectedDate)}
                  </button>
                </li>
                <li>
                  <button onclick={() => exportStudentReport(false)}>
                    <FileCheck class="w-4 h-4" />
                    Thống kê tổng hợp (tất cả)
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Legend -->
        <div class="flex flex-wrap gap-3 text-xs mb-2">
          {#each Object.entries(statusConfig).filter(([key]) => !["present"].includes(key)) as [key, config]}
            <div class="flex items-center gap-1.5">
              <span
                class={`w-2.5 h-2.5 rounded-full ${config.badgeClass.replace("badge-", "bg-")}`}
              ></span>
              <span class="text-base-content/70">{config.label}</span>
            </div>
          {/each}
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto">
        <table class="table table-sm">
          <thead>
            <tr class="bg-base-200/50">
              <th class="font-semibold min-w-[200px]">Học sinh</th>
              <th class="text-center font-semibold w-20">
                <div class="flex flex-col items-center">
                  <ScanFace class="w-4 h-4 mb-0.5" />
                  <span class="text-[10px]">Face ID</span>
                </div>
              </th>
              {#each { length: TOTAL_SESSIONS } as _, i}
                {@const stats = sessionStats[i]}
                <th class="text-center font-semibold min-w-[90px]">
                  <div class="flex flex-col items-center gap-0.5">
                    <span>Tiết {i + 1}</span>
                    <div class="flex gap-1 text-[10px] font-normal">
                      <span class="text-success">{stats.present}</span>
                      <span class="text-base-content/30">|</span>
                      <span class="text-warning">{stats.late}</span>
                      <span class="text-base-content/30">|</span>
                      <span class="text-error">{stats.absent}</span>
                    </div>
                  </div>
                </th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each filteredStudents as student, idx (student.id)}
              {@const studentRecords = attendanceByStudent[student.id] || []}
              <tr
                class="hover:bg-base-200/50 transition-colors {idx % 2 === 0
                  ? ''
                  : 'bg-base-200/20'}"
              >
                <td>
                  <div class="flex items-center gap-3">
                    <div class="avatar placeholder">
                      <div
                        class="w-9 h-9 rounded-full bg-primary/10 text-primary font-semibold flex items-center justify-center"
                      >
                        <span class="text-xs">{getInitials(student)}</span>
                      </div>
                    </div>
                    <div>
                      <p class="font-medium text-base-content leading-tight">
                        {getStudentDisplayName(student)}
                      </p>
                      <p class="text-xs text-base-content/50 font-mono">
                        {student.id}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="text-center">
                  {#if student.face_registered}
                    <div
                      class="badge badge-success badge-sm gap-1"
                      title="Đã đăng ký khuôn mặt"
                    >
                      <Check class="w-3 h-3" />
                    </div>
                  {:else}
                    <div
                      class="badge badge-warning badge-sm gap-1"
                      title="Chưa đăng ký khuôn mặt"
                    >
                      <AlertCircle class="w-3 h-3" />
                    </div>
                  {/if}
                </td>

                {#each { length: TOTAL_SESSIONS } as _, i}
                  {@const sessionNumber = i + 1}
                  {@const record = studentRecords.find(
                    (r: AttendanceRecord) => r.session_number === sessionNumber,
                  )}
                  {@const status = getStatusInfo(record?.attendance_status)}

                  <td class="text-center p-1">
                    <form
                      method="POST"
                      action="?/updateAttendance"
                      use:enhance={() => {
                        isUpdating = true;
                        return async ({ result }) => {
                          isUpdating = false;
                          if (result.type === "success") {
                            showToast({
                              message: "Đã cập nhật",
                              type: "success",
                            });
                            await invalidateAll();
                          } else if (result.type === "failure") {
                            showToast({
                              message: "Cập nhật thất bại",
                              type: "error",
                            });
                          }
                        };
                      }}
                    >
                      <input
                        type="hidden"
                        name="studentId"
                        value={student.id}
                      />
                      <input type="hidden" name="date" value={selectedDate} />
                      <input
                        type="hidden"
                        name="session"
                        value={sessionNumber}
                      />

                      <select
                        name="status"
                        class={`select select-primary select-xs w-full max-w-[80px] font-medium ${status.bgColor} ${status.color} border-0  focus:outline-primary`}
                        onchange={(e) => e.currentTarget.form?.requestSubmit()}
                        disabled={isUpdating}
                      >
                        <option
                          value="on_time"
                          selected={record?.attendance_status === "on_time" ||
                            record?.attendance_status === "present"}
                        >
                          Có mặt
                        </option>
                        <option
                          value="late"
                          selected={record?.attendance_status === "late"}
                        >
                          Đi muộn
                        </option>
                        <option
                          value="absent"
                          selected={!record ||
                            record.attendance_status === "absent"}
                        >
                          Vắng
                        </option>
                        <option
                          value="excused"
                          selected={record?.attendance_status === "excused"}
                        >
                          Có phép
                        </option>
                        <option
                          value="left_early"
                          selected={record?.attendance_status === "left_early"}
                        >
                          Về sớm
                        </option>
                      </select>
                    </form>
                  </td>
                {/each}
              </tr>
            {/each}

            {#if filteredStudents.length === 0}
              <tr>
                <td colspan={TOTAL_SESSIONS + 2} class="text-center py-12">
                  <div class="flex flex-col items-center gap-2">
                    {#if searchQuery}
                      <Search class="w-10 h-10 text-base-content/20" />
                      <p class="text-base-content/60">
                        Không tìm thấy học sinh "{searchQuery}"
                      </p>
                      <button
                        class="btn btn-sm btn-ghost"
                        onclick={() => (searchQuery = "")}
                      >
                        Xóa tìm kiếm
                      </button>
                    {:else}
                      <Users class="w-10 h-10 text-base-content/20" />
                      <p class="text-base-content/60">
                        Chưa có học sinh trong lớp này
                      </p>
                      <button
                        class="btn btn-sm btn-primary"
                        onclick={() => (showAddModal = true)}
                      >
                        Thêm học sinh
                      </button>
                    {/if}
                  </div>
                </td>
              </tr>
            {/if}
          </tbody>
        </table>
      </div>

      <!-- Footer -->
      <div class="card-body p-4 pt-2 border-t border-base-200">
        <div
          class="flex flex-wrap justify-between items-center gap-2 text-sm text-base-content/60"
        >
          <span>
            Hiển thị {filteredStudents.length} / {totalStudents} học sinh
          </span>
          <div class="flex items-center gap-4">
            <span class="flex items-center gap-1">
              <BarChart3 class="w-4 h-4" />
              Tỷ lệ đi học:
              <strong class="text-base-content">{attendanceRate}%</strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Add Student Modal -->
<dialog class="modal" class:modal-open={showAddModal}>
  <div class="modal-box max-w-md">
    <button
      class="btn btn-sm btn-circle btn-ghost absolute right-3 top-3"
      onclick={() => (showAddModal = false)}
    >
      <X class="w-4 h-4" />
    </button>

    <h3 class="font-bold text-lg flex items-center gap-2 mb-1">
      <div class="bg-primary/10 p-2 rounded-lg">
        <UserPlus class="w-5 h-5 text-primary" />
      </div>
      Thêm học sinh
    </h3>
    <p class="text-sm text-base-content/60 mb-4">
      Thêm học sinh vào lớp {data.classDetail.name}
    </p>

    <form
      method="POST"
      action="?/addStudent"
      use:enhance={() => {
        return async ({ result }) => {
          if (result.type === "success") {
            showAddModal = false;
            showToast({ message: "Đã thêm học sinh!", type: "success" });
            await invalidateAll();
          } else if (result.type === "failure") {
            showToast({ message: "Thêm học sinh thất bại", type: "error" });
          }
        };
      }}
    >
      <div class="form-control mb-4">
        <label for="studentId" class="label">
          <span class="label-text font-medium">Mã học sinh</span>
        </label>
        <input
          type="text"
          id="studentId"
          name="studentId"
          placeholder="Nhập mã học sinh đã có trong hệ thống..."
          class="input input-bordered w-full"
          required
        />
        <label class="label">
          <span class="label-text-alt text-base-content/50">
            Học sinh phải được tạo trước trong hệ thống quản lý
          </span>
        </label>
      </div>

      <div class="modal-action">
        <button
          type="button"
          class="btn btn-ghost"
          onclick={() => (showAddModal = false)}
        >
          Hủy
        </button>
        <button type="submit" class="btn btn-primary">
          <UserPlus class="w-4 h-4" />
          Thêm học sinh
        </button>
      </div>
    </form>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button onclick={() => (showAddModal = false)}>close</button>
  </form>
</dialog>
