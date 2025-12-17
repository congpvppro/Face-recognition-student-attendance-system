<script lang="ts">
  let { records, pagination, studentId } = $props();
  
  const statusColors = {
    on_time: 'badge-success',
    late: 'badge-warning',
    absent: 'badge-error',
    excused: 'badge-info'
  };
  
  function formatTime(time: string | null) {
    if (!time) return '-';
    return time.substring(0, 5); // HH:MM
  }
</script>
<div class="overflow-x-auto">
  <table class="table table-zebra w-full">
    <thead>
      <tr>
        <th>Date</th>
        <th>Session</th>
        <th>Entry Time</th>
        <th>Exit Time</th>
        <th>Duration</th>
        <th>Status</th>
        <th>Late (min)</th>
        <th>Score</th>
      </tr>
    </thead>
    <tbody>
      {#each records as record}
        <tr>
          <td>{record.session_date}</td>
          <td>Session {record.session_number}</td>
          <td>{formatTime(record.entry_time)}</td>
          <td>{formatTime(record.exit_time)}</td>
          <td>{record.duration_minutes || 0} min</td>
          <td>
            <span class="badge {statusColors[record.attendance_status]} badge-sm">
              {record.attendance_status}
            </span>
          </td>
          <td>{record.late_minutes || 0}</td>
          <td>{record.attendance_score?.toFixed(1) || '-'}</td>
        </tr>
      {/each}
    </tbody>
  </table>
  
  <!-- Pagination -->
  {#if pagination.total_pages > 1}
    <div class="flex justify-center gap-2 mt-4">
      <div class="join">
        {#each Array(pagination.total_pages) as _, i}
          <a 
            href="?page={i + 1}"
            class="join-item btn btn-sm {pagination.page === i + 1 ? 'btn-active' : ''}"
          >
            {i + 1}
          </a>
        {/each}
      </div>
    </div>
  {/if}
</div>