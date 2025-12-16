<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/state";
  import { Users, School, ArrowRight } from "lucide-svelte";

  let { data } = $props();
</script>

<div class="container mx-auto p-6 max-w-7xl">
  <div class="mb-8">
    <h1 class="text-3xl font-bold font-montserrat text-gray-900">
      Lớp chủ nhiệm
    </h1>
    <p class="text-gray-600 mt-2">Quản lý lớp học và điểm danh học sinh</p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {#each data.classes as cls}
      <a
        href="/teacher/classes/{cls.id}"
        class="group bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all hover:-translate-y-1 block"
      >
        <div class="flex justify-between items-start mb-4">
          <div
            class="bg-blue-50 p-3 rounded-lg group-hover:bg-blue-100 transition-colors"
          >
            <School class="text-blue-600 w-6 h-6" />
          </div>
          <span
            class="bg-gray-100 text-gray-600 text-xs font-semibold px-2.5 py-0.5 rounded-full"
          >
            ID: {cls.id}
          </span>
        </div>

        <h3 class="text-xl font-bold text-gray-900 mb-2">{cls.name}</h3>

        <div class="flex items-center text-gray-500 text-sm mb-6">
          <Users class="w-4 h-4 mr-2" />
          <span>{cls.students.length} Học sinh</span>
        </div>

        <div
          class="flex items-center text-blue-600 font-medium text-sm group-hover:translate-x-1 transition-transform"
        >
          Xem chi tiết
          <ArrowRight class="w-4 h-4 ml-1" />
        </div>
      </a>
    {/each}

    {#if data.classes.length === 0}
      <div
        class="col-span-full text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300"
      >
        <School class="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <h3 class="text-lg font-medium text-gray-900">Chưa có lớp học</h3>
        <p class="text-gray-500">Bạn chưa được phân công chủ nhiệm lớp nào.</p>
      </div>
    {/if}
  </div>
</div>
