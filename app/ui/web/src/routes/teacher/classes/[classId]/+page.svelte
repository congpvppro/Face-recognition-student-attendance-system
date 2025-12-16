<script lang="ts">
  import { enhance } from "$app/forms";
  import {
    Users,
    UserPlus,
    BarChart3,
    Calendar,
    CheckCircle2,
    AlertCircle,
    Clock,
  } from "lucide-svelte";
  import type { PageData } from "./$types";

  // Total sessions per day (matching Python DB class_schedule)
  const TOTAL_SESSIONS = 5;

  let { data, form }: { data: PageData } = $props();

  let showAddModal = $state(false);

  // Group all attendance records by student ID for efficient lookup
  const attendanceByStudent = $derived.by(() => {
    return data.attendance.reduce(
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
  });

  // Calculate overall attendance stats
  const totalStudents = $derived(data.classDetail.students.length);

  const studentsPresentToday = $derived.by(() => {
    const presentStudentIds = new Set<string>();
    for (const record of data.attendance) {
      if (
        record.attendance_status !== "absent" &&
        record.attendance_status !== undefined
      ) {
        presentStudentIds.add(record.student_id);
      }
    }
    return presentStudentIds.size;
  });

  const attendanceRate = $derived(
    totalStudents > 0
      ? Math.round((studentsPresentToday / totalStudents) * 100)
      : 0,
  );

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
      default:
        return {
          label: "Không rõ",
          icon: null,
          color: "text-gray-500",
          bgColor: "bg-gray-100",
        };
    }
  };
</script>

<div class="container mx-auto p-6 max-w-7xl">
  <!-- Header -->
  <div
    class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4"
  >
    <div>
      <div class="flex items-center gap-2 text-sm text-gray-500 mb-1">
        <a href="/teacher/classes" class="hover:text-blue-600">Lớp học</a>
        <span>/</span>
        <span>{data.classDetail.name}</span>
      </div>
      <h1 class="text-3xl font-bold font-montserrat text-gray-900">
        {data.classDetail.name}
      </h1>
      <p class="text-gray-600 mt-1">
        Giáo viên: {data.classDetail.teacher || "Chưa phân công"}
      </p>
    </div>
    <div class="flex gap-3">
      <button
        class="btn btn-primary gap-2 text-white"
        onclick={() => (showAddModal = true)}
      >
        <UserPlus class="w-4 h-4" />
        Thêm học sinh
      </button>
    </div>
  </div>

  <!-- Stats Cards -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
      <div class="flex items-center gap-4">
        <div class="bg-blue-50 p-3 rounded-lg">
          <Users class="text-blue-600 w-6 h-6" />
        </div>
        <div>
          <p class="text-sm text-gray-500 font-medium">Tổng số học sinh</p>
          <h3 class="text-2xl font-bold text-gray-900">{totalStudents}</h3>
        </div>
      </div>
    </div>
    <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
      <div class="flex items-center gap-4">
        <div class="bg-green-50 p-3 rounded-lg">
          <Calendar class="text-green-600 w-6 h-6" />
        </div>
        <div>
          <p class="text-sm text-gray-500 font-medium">Điểm danh hôm nay</p>
          <h3 class="text-2xl font-bold text-gray-900">
            {studentsPresentToday} / {totalStudents}
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
          <p class="text-sm text-gray-500 font-medium">Tỷ lệ chuyên cần</p>
          <h3 class="text-2xl font-bold text-gray-900">{attendanceRate}%</h3>
        </div>
      </div>
    </div>
  </div>

  <!-- Students List -->
  <div
    class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
  >
    <div class="p-6 border-b border-gray-200 flex justify-between items-center">
      <h3 class="text-lg font-bold text-gray-900">
        Chi tiết điểm danh hôm nay
      </h3>
      <input
        type="date"
        class="input input-sm input-bordered"
        value={new Date().toISOString().split("T")[0]}
        change={(e) => {
          // TODO: Implement date change handler to refetch data
          // This will require modifying the load function to accept a date parameter
          // and invalidating the data.
          // For now, it defaults to today.
        }}
      />
    </div>

    <div class="overflow-x-auto">
      <table class="table w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="w-1/4">Học sinh</th>
            <th class="text-center">Tiết 1</th>
            <th class="text-center">Tiết 2</th>
            <th class="text-center">Tiết 3</th>
            <th class="text-center">Tiết 4</th>
            <th class="text-center">Tiết 5</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each data.classDetail.students as student}
            {@const studentRecords = attendanceByStudent[student.id] || []}
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="font-medium">
                <div class="flex flex-col">
                  <span class="font-bold text-gray-900"
                    >{student.first_name} {student.last_name}</span
                  >
                  <span class="font-mono text-xs text-gray-500"
                    >{student.id}</span
                  >
                </div>
              </td>

              <!-- Display status for each session -->
              {#each { length: TOTAL_SESSIONS } as _, i}
                {@const sessionNumber = i + 1}
                {@const record = studentRecords.find(
                  (r: any) => r.session_number === sessionNumber,
                )}
                {@const status = getStatusInfo(record?.attendance_status)}

                <td class="text-center">
                  <form
                    method="POST"
                    action="?/updateAttendance"
                    use:enhance
                    class="group"
                  >
                    <input type="hidden" name="studentId" value={student.id} />
                    <input
                      type="hidden"
                      name="date"
                      value={new Date().toISOString().split("T")[0]}
                    />
                    <input type="hidden" name="session" value={sessionNumber} />

                    <select
                      name="status"
                      class={`select select-xs select-ghost font-semibold border-none group-hover:bg-base-200 ${status.color}`}
                      onchange={(e) => e.currentTarget.form?.requestSubmit()}
                    >
                      <option
                        value="on_time"
                        selected={record?.attendance_status === "on_time" ||
                          record?.attendance_status === "present"}
                        >Có mặt</option
                      >
                      <option
                        value="late"
                        selected={record?.attendance_status === "late"}
                        >Đi muộn</option
                      >
                      <option
                        value="absent"
                        selected={!record ||
                          record.attendance_status === "absent"}>Vắng</option
                      >
                      <option
                        value="excused"
                        selected={record?.attendance_status === "excused"}
                        >Có phép</option
                      >
                    </select>
                  </form>
                </td>
              {/each}
            </tr>
          {/each}
          {#if data.classDetail.students.length === 0}
            <tr>
              <td colspan="6" class="text-center py-8 text-gray-500">
                Chưa có học sinh nào trong lớp này.
              </td>
            </tr>
          {/if}
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- Add Student Modal -->
{#if showAddModal}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
  >
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
      <div class="p-6 border-b border-gray-100">
        <h3 class="text-lg font-bold text-gray-900">Thêm học sinh vào lớp</h3>
      </div>
      <form
        method="POST"
        action="?/addStudent"
        use:enhance={() => {
          return async ({ result }) => {
            if (result.type === "success") showAddModal = false;
          };
        }}
      >
        <div class="p-6 space-y-4">
          <div class="form-control">
            <label class="label font-medium text-gray-700"
              >Mã học sinh (ID)</label
            >
            <input
              type="text"
              name="studentId"
              placeholder="Nhập mã học sinh..."
              class="input input-bordered w-full focus:input-primary"
              required
            />
            <p class="text-xs text-gray-500 mt-1">
              Nhập ID của học sinh đã tồn tại trong hệ thống.
            </p>
          </div>
        </div>
        <div class="p-6 bg-gray-50 flex justify-end gap-3">
          <button
            type="button"
            class="btn btn-ghost"
            onclick={() => (showAddModal = false)}>Hủy bỏ</button
          >
          <button type="submit" class="btn btn-primary text-white"
            >Thêm học sinh</button
          >
        </div>
      </form>
    </div>
  </div>
{/if}
