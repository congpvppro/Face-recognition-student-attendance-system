<script lang="ts">
  import { User, TrendingUp, AlertCircle, Target, Calendar } from 'lucide-svelte';
  import AttendanceGraph from '$lib/components/AttendanceGraph.svelte';
  import AnalysisCard from '$lib/components/AnalysisCard.svelte';
  import InterventionTimeline from '$lib/components/InterventionTimeline.svelte';
  import AttendanceTable from '$lib/components/AttendanceTable.svelte';
  let { data } = $props();
</script>
<svelte:head>
  <title>{data.student.name} - Student Profile</title>
</svelte:head>
<div class="min-h-screen bg-base-200 py-8 px-4">
  <div class="container mx-auto max-w-7xl">
    
    <!-- 1. HEADER BLOCK -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="flex items-center gap-6">
          <div class="avatar placeholder">
            <div class="bg-primary text-primary-content rounded-full w-24">
              <span class="text-3xl font-bold">
                {data.student.first_name?.[0] || data.student.name?.[0]}
              </span>
            </div>
          </div>
          
          <div class="flex-1">
            <h1 class="text-3xl font-bold">
              {data.student.first_name} {data.student.last_name}
            </h1>
            <p class="text-base-content/60 mt-1">
              Student ID: <span class="font-mono">{data.student.id}</span>
            </p>
            <div class="flex gap-2 mt-2">
              <span class="badge badge-outline">Class {data.student.class_id}</span>
              {#if data.student.face_registered}
                <span class="badge badge-success">Face Registered</span>
              {:else}
                <span class="badge badge-warning">No Face Data</span>
              {/if}
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 2. STATISTICS CARDS BLOCK -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="stat bg-base-100 shadow rounded-lg">
        <div class="stat-figure text-primary">
          <TrendingUp size={32} />
        </div>
        <div class="stat-title">Attendance Rate</div>
        <div class="stat-value text-primary">{data.statistics.attendance_rate}%</div>
        <div class="stat-desc">Overall performance</div>
      </div>
      <div class="stat bg-base-100 shadow rounded-lg">
        <div class="stat-title">Present</div>
        <div class="stat-value text-success">
          {data.statistics.on_time_count}
        </div>
        <div class="stat-desc">
          of {data.statistics.total_sessions} sessions
        </div>
      </div>
      <div class="stat bg-base-100 shadow rounded-lg">
        <div class="stat-title">Late</div>
        <div class="stat-value text-warning">{data.statistics.late_count}</div>
        <div class="stat-desc">Times late to class</div>
      </div>
      <div class="stat bg-base-100 shadow rounded-lg">
        <div class="stat-title">Absent</div>
        <div class="stat-value text-error">{data.statistics.absent_count}</div>
        <div class="stat-desc">Missed sessions</div>
      </div>
    </div>
    <!-- 3. ATTENDANCE GRAPH BLOCK -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <h2 class="card-title text-2xl mb-4">
          <TrendingUp class="text-primary" />
          Attendance Trend (Last 30 Days)
        </h2>
        <AttendanceGraph data={data.graphData} />
      </div>
    </div>
    <!-- 4. AI ANALYSIS BLOCK -->
    {#if data.analysis && data.analysis.length > 0}
      <div class="card bg-base-100 shadow-xl mb-6">
        <div class="card-body">
          <h2 class="card-title text-2xl mb-4">
            <AlertCircle class="text-warning" />
            AI Analysis & Alerts
          </h2>
          <div class="space-y-3">
            {#each data.analysis as item}
              <AnalysisCard analysis={item} />
            {/each}
          </div>
        </div>
      </div>
    {/if}
    <!-- 5. INTERVENTION HISTORY BLOCK -->
    {#if data.interventions && data.interventions.length > 0}
      <div class="card bg-base-100 shadow-xl mb-6">
        <div class="card-body">
          <h2 class="card-title text-2xl mb-4">
            <Target class="text-info" />
            Intervention History
          </h2>
          <InterventionTimeline interventions={data.interventions} />
        </div>
      </div>
    {/if}
    <!-- 6. ATTENDANCE TABLE BLOCK -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-2xl mb-4">
          <Calendar class="text-secondary" />
          Detailed Attendance History
        </h2>
        <AttendanceTable 
          records={data.attendanceHistory}
          pagination={data.pagination}
          studentId={data.student.id}
        />
      </div>
    </div>
  </div>
</div>