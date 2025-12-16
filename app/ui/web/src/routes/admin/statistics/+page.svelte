<script lang="ts">
  import { BarChart3, Users, Filter } from "lucide-svelte";
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
</script>

<div class="container mx-auto p-6 max-w-7xl">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold font-montserrat text-gray-900">
      Thống kê chuyên cần
    </h1>
    <p class="text-gray-600 mt-1">
      Xem và lọc báo cáo điểm danh theo lớp và ngày.
    </p>
  </div>

  <!-- Filter Controls -->
  <div
    class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm mb-8 flex flex-col md:flex-row gap-4 items-center"
  >
    <div class="form-control w-full md:w-1/3">
      <label class="label"
        ><span class="label-text font-medium">Chọn lớp</span></label
      >
      <select bind:value={selectedClassIdLocal} class="select select-bordered">
        <option value={null} disabled>-- Lớp --</option>
        {#each data.classes as cls}
          <option value={cls.id}>{cls.name}</option>
        {/each}
      </select>
    </div>
    <div class="form-control w-full md:w-1/3">
      <label class="label"
        ><span class="label-text font-medium">Chọn ngày</span></label
      >
      <input
        type="date"
        bind:value={selectedDateLocal}
        class="input input-bordered"
      />
    </div>
    <div class="form-control w-full md:w-auto mt-auto">
      <button
        class="btn btn-primary text-white w-full"
        onclick={applyFilters}
        disabled={!selectedClassIdLocal}
      >
        <Filter class="w-4 h-4" />
        Xem báo cáo
      </button>
    </div>
  </div>

  <!-- Stats Cards -->
  {#if data.selectedClassId && data.students.length > 0}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div class="flex items-center gap-4">
          <div class="bg-blue-50 p-3 rounded-lg">
            <Users class="text-blue-600 w-6 h-6" />
          </div>
          <div>
            <p class="text-sm text-gray-500 font-medium">Sĩ số</p>
            <h3 class="text-2xl font-bold text-gray-900">
              {data.students.length}
            </h3>
          </div>
        </div>
      </div>
      <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div class="flex items-center gap-4">
          <div class="bg-purple-50 p-3 rounded-lg">
            <BarChart3 class="text-purple-600 w-6 h-6" />
          </div>
          <div>
            <p class="text-sm text-gray-500 font-medium">
              Tỉ lệ chuyên cần trung bình
            </p>
            <h3 class="text-2xl font-bold text-gray-900">
              {overallAttendanceRate}%
            </h3>
          </div>
        </div>
      </div>
      <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div class="flex items-center gap-4">
          <div class="bg-green-50 p-3 rounded-lg">
            <Users class="text-green-600 w-6 h-6" />
          </div>
          <div>
            <p class="text-sm text-gray-500 font-medium">
              Tổng số tiết học (Có mặt/Muộn/Vắng)
            </p>
            <div class="flex items-baseline gap-2 font-bold">
              <span class="text-success" title="Present"
                >{totalPresentSessions}</span
              >
              <span>/</span>
              <span class="text-warning" title="Late">{totalLateSessions}</span>
              <span>/</span>
              <span class="text-error" title="Absent"
                >{totalAbsentSessions}</span
              >
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- Student Statistics Table -->
  {#if data.selectedClassId}
    <div
      class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
    >
      <div class="p-6 border-b border-gray-200">
        <h3 class="text-lg font-bold text-gray-900">
          Báo cáo ngày {new Date(data.selectedDate).toLocaleDateString("vi-VN")}
        </h3>
      </div>
      <div class="overflow-x-auto">
        {#if data.students.length > 0}
          <table class="table w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th>Học sinh</th>
                <th class="text-center">Có mặt</th>
                <th class="text-center">Đi muộn</th>
                <th class="text-center">Vắng</th>
                <th class="text-center">Tỉ lệ (%)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              {#each studentStats as stat}
                <tr class="hover:bg-gray-50">
                  <td class="font-medium">
                    <div class="flex flex-col">
                      <span class="font-bold text-gray-900"
                        >{stat.first_name} {stat.last_name}</span
                      >
                      <span class="font-mono text-xs text-gray-500"
                        >{stat.id}</span
                      >
                    </div>
                  </td>
                  <td class="text-center font-semibold text-success"
                    >{stat.present}</td
                  >
                  <td class="text-center font-semibold text-warning"
                    >{stat.late}</td
                  >
                  <td class="text-center font-semibold text-error"
                    >{stat.absent}</td
                  >
                  <td class="text-center">
                    <div
                      class="radial-progress text-primary"
                      style="--value:{stat.rate}; --size:2.5rem; --thickness: 4px;"
                    >
                      {stat.rate}%
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        {:else}
          <p class="text-center py-8 text-gray-500">
            Không có học sinh trong lớp này để hiển thị thống kê.
          </p>
        {/if}
      </div>
    </div>
  {:else}
    <div class="text-center py-20 bg-gray-50 rounded-lg border-2 border-dashed">
      <BarChart3 class="w-12 h-12 mx-auto text-gray-400 mb-2" />
      <h3 class="font-bold text-lg">
        Vui lòng chọn lớp và ngày để xem thống kê
      </h3>
      <p class="text-sm text-gray-500">
        Dữ liệu điểm danh sẽ được tổng hợp tại đây.
      </p>
    </div>
  {/if}
</div>
