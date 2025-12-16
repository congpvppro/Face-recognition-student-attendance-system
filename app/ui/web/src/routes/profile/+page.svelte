<script lang="ts">
  import { User, School, Calendar, Mail, UserCheck } from "lucide-svelte";

  let { data } = $props();
</script>

<svelte:head>
  <title>Hồ sơ cá nhân - Attendde</title>
</svelte:head>

<div class="min-h-screen bg-base-200 py-10 px-4">
  <div class="container mx-auto max-w-4xl">
    <!-- Profile Header -->
    <div class="card bg-base-100 shadow-xl mb-8 overflow-visible">
      <div class="h-32 bg-primary/10 rounded-t-xl relative">
        <div class="absolute -bottom-10 left-8">
          <div class="avatar placeholder">
            <div
              class="bg-primary text-primary-content rounded-full w-24 ring ring-base-100 ring-offset-2 flex items-center justify-center"
            >
              <span class="text-3xl font-bold">{data.user.first_name[0]}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="card-body pt-12">
        <div
          class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
        >
          <div>
            <h1 class="text-3xl font-bold">
              {data.user.first_name}
              {data.user.last_name}
            </h1>
            <p class="text-base-content/60 flex items-center gap-2 mt-1">
              <span
                class="badge badge-outline uppercase text-xs font-bold tracking-wider"
              >
                {data.user.role}
              </span>
              <span>@{data.user.username}</span>
            </p>
          </div>
          <div class="flex gap-2">
            <!-- Potential Action Buttons -->
          </div>
        </div>

        <div class="divider"></div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="flex items-center gap-3 p-3 rounded-lg bg-base-200/50">
            <div class="p-2 bg-primary/10 text-primary rounded-lg">
              <Mail size={20} />
            </div>
            <div>
              <p class="text-xs text-base-content/60 font-medium uppercase">
                Địa chỉ Email
              </p>
              <p class="font-medium">{data.user.email}</p>
            </div>
          </div>

          <div class="flex items-center gap-3 p-3 rounded-lg bg-base-200/50">
            <div class="p-2 bg-primary/10 text-primary rounded-lg">
              <Calendar size={20} />
            </div>
            <div>
              <p class="text-xs text-base-content/60 font-medium uppercase">
                Ngày sinh
              </p>
              <p class="font-medium">{data.user.dob || "Chưa cung cấp"}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    {#if data.user.role === "parent"}
      <!-- Students Section -->
      <div class="mb-6 flex items-center gap-3">
        <div class="p-2 bg-secondary/10 text-secondary rounded-lg">
          <School size={24} />
        </div>
        <h2 class="text-2xl font-bold">Con em của bạn</h2>
      </div>

      {#if data.students.length > 0}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          {#each data.students as student}
            <div
              class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow border border-base-200"
            >
              <div class="card-body">
                <div class="flex items-start justify-between">
                  <div class="flex items-center gap-4">
                    <div class="avatar placeholder">
                      <div
                        class="bg-secondary text-secondary-content rounded-xl w-16"
                      >
                        <span class="text-2xl font-bold"
                          >{student.first_name[0]}</span
                        >
                      </div>
                    </div>
                    <div>
                      <h3 class="card-title text-lg">
                        {student.first_name}
                        {student.last_name}
                      </h3>
                      <p class="text-sm text-base-content/60">
                        ID: <span class="font-mono">{student.id}</span>
                      </p>
                    </div>
                  </div>
                  <div class="badge badge-success gap-1">
                    <UserCheck size={12} />
                    Đang học
                  </div>
                </div>

                <div class="divider my-2"></div>

                <div class="grid grid-cols-2 gap-2 text-sm">
                  <div class="flex flex-col">
                    <span class="text-base-content/50 text-xs">Lớp</span>
                    <span class="font-medium">{student.class_id || "N/A"}</span>
                  </div>
                  <div class="flex flex-col">
                    <span class="text-base-content/50 text-xs">Ngày sinh</span>
                    <span class="font-medium">{student.dob || "N/A"}</span>
                  </div>
                </div>

                <div class="card-actions justify-end mt-4">
                  <button class="btn btn-sm btn-outline btn-secondary"
                    >Xem điểm danh</button
                  >
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="alert shadow-lg">
          <School size={24} class="text-info" />
          <div>
            <h3 class="font-bold">Chưa liên kết học sinh nào!</h3>
            <div class="text-xs">
              Vui lòng liên hệ quản trị viên nhà trường để liên kết tài khoản
              với con em của bạn.
            </div>
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>
