<script lang="ts">
    import { goto } from "$app/navigation";
    import { page } from "$app/stores";

    let { data } = $props();

    // State
    let searchQuery = $state("");
    let sortColumn = $state<string>("student_name");
    let sortDirection = $state<"asc" | "desc">("asc");

    // Handle file selection
    async function selectFile(filename: string) {
        await goto(`/admin/attendance-summary?file=${filename}`);
    }

    // Sorting function
    function sort(column: string) {
        if (sortColumn === column) {
            sortDirection = sortDirection === "asc" ? "desc" : "asc";
        } else {
            sortColumn = column;
            sortDirection = "asc";
        }
    }

    // Filtered and sorted data
    const filteredData = $derived.by(() => {
        let filtered = data.data;

        // Search filter
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(
                (s: any) =>
                    s.student_name.toLowerCase().includes(query) ||
                    s.student_id.toLowerCase().includes(query),
            );
        }

        // Sort
        filtered = [...filtered].sort((a: any, b: any) => {
            let aVal = a[sortColumn];
            let bVal = b[sortColumn];

            // Handle percentage strings
            if (sortColumn === "attendance_percent") {
                aVal = parseFloat(aVal.replace("%", ""));
                bVal = parseFloat(bVal.replace("%", ""));
            }

            if (typeof aVal === "string") {
                return sortDirection === "asc"
                    ? aVal.localeCompare(bVal)
                    : bVal.localeCompare(aVal);
            } else {
                return sortDirection === "asc" ? aVal - bVal : bVal - aVal;
            }
        });

        return filtered;
    });

    // Export to CSV
    function exportToCSV() {
        const headers = [
            "Mã HS",
            "Họ tên",
            "Tổng buổi",
            "Có mặt",
            "Vắng",
            "Đi muộn",
            "Tỷ lệ %",
        ];
        const rows = filteredData.map((s: any) => [
            s.student_id,
            s.student_name,
            s.total_sessions,
            s.attended,
            s.absent,
            s.late,
            s.attendance_percent,
        ]);

        const csvContent = [
            headers.join(","),
            ...rows.map((r) => r.join(",")),
        ].join("\n");

        const blob = new Blob([csvContent], {
            type: "text/csv;charset=utf-8;",
        });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `attendance_summary_${new Date().toISOString().split("T")[0]}.csv`;
        link.click();
    }
</script>

<!-- Header -->
<div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold">Báo Cáo Tổng Hợp Điểm Danh</h1>

    <!-- File Selector -->
    <select
        class="select select-bordered w-64"
        value={data.currentFile}
        onchange={(e) => selectFile(e.currentTarget.value)}
    >
        {#each data.csvFiles as file}
            <option value={file.filename}>{file.display_name}</option>
        {/each}
    </select>
</div>

<!-- Summary Cards -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
    <div class="stat bg-base-200 rounded-lg">
        <div class="stat-title">Tổng số học sinh</div>
        <div class="stat-value text-primary">{data.summary.total_students}</div>
    </div>
    <div class="stat bg-base-200 rounded-lg">
        <div class="stat-title">Tỷ lệ điểm danh trung bình</div>
        <div class="stat-value text-success">{data.summary.avg_attendance}</div>
    </div>
    <div class="stat bg-base-200 rounded-lg">
        <div class="stat-title">Số buổi trung bình</div>
        <div class="stat-value">{data.summary.avg_sessions}</div>
    </div>
</div>

<!-- Search & Export -->
<div class="flex gap-4 mb-4">
    <input
        type="search"
        bind:value={searchQuery}
        placeholder="Tìm học sinh theo tên hoặc mã..."
        class="input input-bordered flex-1"
    />
    <button class="btn btn-primary" onclick={exportToCSV}>
        <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
        >
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
        </svg>
        Xuất CSV
    </button>
</div>

<!-- Data Table -->
<div class="overflow-x-auto bg-base-100 rounded-lg shadow">
    <table class="table table-zebra">
        <thead>
            <tr>
                <th class="cursor-pointer" onclick={() => sort("student_id")}>
                    Mã HS
                    {#if sortColumn === "student_id"}
                        <span>{sortDirection === "asc" ? "↑" : "↓"}</span>
                    {/if}
                </th>
                <th class="cursor-pointer" onclick={() => sort("student_name")}>
                    Họ tên
                    {#if sortColumn === "student_name"}
                        <span>{sortDirection === "asc" ? "↑" : "↓"}</span>
                    {/if}
                </th>
                <th
                    class="cursor-pointer text-center"
                    onclick={() => sort("total_sessions")}
                >
                    Tổng buổi
                    {#if sortColumn === "total_sessions"}
                        <span>{sortDirection === "asc" ? "↑" : "↓"}</span>
                    {/if}
                </th>
                <th
                    class="cursor-pointer text-center"
                    onclick={() => sort("attended")}
                >
                    Có mặt
                    {#if sortColumn === "attended"}
                        <span>{sortDirection === "asc" ? "↑" : "↓"}</span>
                    {/if}
                </th>
                <th
                    class="cursor-pointer text-center"
                    onclick={() => sort("absent")}
                >
                    Vắng
                    {#if sortColumn === "absent"}
                        <span>{sortDirection === "asc" ? "↑" : "↓"}</span>
                    {/if}
                </th>
                <th
                    class="cursor-pointer text-center"
                    onclick={() => sort("late")}
                >
                    Đi muộn
                    {#if sortColumn === "late"}
                        <span>{sortDirection === "asc" ? "↑" : "↓"}</span>
                    {/if}
                </th>
                <th
                    class="cursor-pointer"
                    onclick={() => sort("attendance_percent")}
                >
                    Tỷ lệ %
                    {#if sortColumn === "attendance_percent"}
                        <span>{sortDirection === "asc" ? "↑" : "↓"}</span>
                    {/if}
                </th>
            </tr>
        </thead>
        <tbody>
            {#if filteredData.length === 0}
                <tr>
                    <td
                        colspan="7"
                        class="text-center py-8 text-base-content/50"
                    >
                        Không có dữ liệu
                    </td>
                </tr>
            {:else}
                {#each filteredData as student}
                    <tr class="hover">
                        <td class="font-mono">{student.student_id}</td>
                        <td>
                            <a
                                href="/student/{student.student_id}"
                                class="link link-primary"
                            >
                                {student.student_name}
                            </a>
                        </td>
                        <td class="text-center">{student.total_sessions}</td>
                        <td class="text-center text-success font-semibold"
                            >{student.attended}</td
                        >
                        <td class="text-center text-error font-semibold"
                            >{student.absent}</td
                        >
                        <td class="text-center text-warning font-semibold"
                            >{student.late}</td
                        >
                        <td>
                            <div class="flex items-center gap-2">
                                <span class="font-semibold"
                                    >{student.attendance_percent}</span
                                >
                                <progress
                                    class="progress progress-success w-20"
                                    value={parseFloat(
                                        student.attendance_percent.replace(
                                            "%",
                                            "",
                                        ),
                                    )}
                                    max="100"
                                ></progress>
                            </div>
                        </td>
                    </tr>
                {/each}
            {/if}
        </tbody>
    </table>
</div>

<!-- Footer -->
<div class="mt-4 text-sm text-base-content/60 text-center">
    Hiển thị {filteredData.length} / {data.data.length} học sinh
</div>
