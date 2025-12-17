<script lang="ts">
  import {
    BarChart3,
    CalendarCheck,
    Camera,
    ChevronDown,
    FileText,
    GraduationCap,
    LogOut,
    Menu,
    School,
    Settings,
    User,
    UserPlus,
    Users,
    Shield,
  } from "lucide-svelte";
  import { page } from "$app/state";

  let { user = null } = $props();
  let currentUser = $derived(user || page.data.user);
  let currentPath = $derived(page.url.pathname);

  console.log("NavigationBar - Current User:", currentUser);

  // Define navigation items based on User Role
  let navItems = $derived.by(() => {
    if (!currentUser) return [];

    switch (currentUser.role) {
      case "admin":
        return [
          { label: "Giáo viên", href: "/admin/teachers", icon: Users },
          { label: "Phụ huynh", href: "/admin/parents", icon: UserPlus },
          { label: "Lớp học", href: "/admin/classes", icon: School },
          { label: "Học sinh", href: "/admin/students", icon: GraduationCap },
          {
            label: "Duyệt khuôn mặt",
            href: "/admin/unregistered",
            icon: UserPlus,
          }, // Face ID Registration
          { label: "Thống kê", href: "/admin/statistics", icon: BarChart3 },
          {
            label: "Báo cáo tổng hợp",
            href: "/admin/attendance-summary",
            icon: FileText,
          },
        ];
      case "teacher":
        return [
          { label: "Lớp chủ nhiệm", href: "/teacher/classes", icon: School },
          { label: "Đơn xin phép", href: "/teacher/tickets", icon: FileText },
          {
            label: "Duyệt khuôn mặt",
            href: "/teacher/unregistered",
            icon: UserPlus,
          },
          { label: "Thống kê", href: "/teacher/statistics", icon: BarChart3 },
        ];
      case "parent":
        return [
          {
            label: "Điểm danh",
            href: "/parent/dashboard",
            icon: CalendarCheck,
          },
          { label: "Gửi đơn", href: "/parent/tickets", icon: FileText },
        ];
      default:
        return [];
    }
  });

  // Helper to get badge color for roles
  const getRoleBadgeClass = (role: string) => {
    switch (role) {
      case "admin":
        return "bg-red-100 text-red-700 border-red-200";
      case "teacher":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "parent":
        return "bg-green-100 text-green-700 border-green-200";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };
</script>

<!-- Hide Navbar specifically on the Kiosk Mode page to prevent students from navigating away -->
{#if !currentPath.startsWith("/attendance")}
  <div
    class="navbar border-base-200/50 bg-base-100/95 fixed inset-x-0 top-0 z-50 h-16 border-b px-3 shadow-sm backdrop-blur transition-all md:px-6"
  >
    <!-- Left: mobile menu + brand -->
    <div class="navbar-start gap-1 md:gap-3">
      <!-- Mobile menu dropdown (Only if logged in) -->
      {#if currentUser}
        <div class="dropdown md:hidden">
          <button
            type="button"
            tabindex="0"
            class="btn btn-ghost btn-circle btn-sm hover:bg-base-200 h-9 w-9"
            aria-label="Mở menu"
          >
            <Menu class="h-5 w-5" />
          </button>

          <ul
            tabindex="-1"
            class="menu menu-sm dropdown-content bg-base-100 rounded-box ring-base-content/5 z-[1] mt-3 w-56 p-2 shadow-lg ring-1"
          >
            {#each navItems as item}
              <li>
                <a
                  href={item.href}
                  class:active={currentPath.startsWith(item.href)}
                  class="gap-3 py-3 font-medium"
                >
                  <svelte:component this={item.icon} class="h-4 w-4" />
                  {item.label}
                </a>
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      <!-- Brand -->
      <a
        href={currentUser
          ? currentUser.role === "parent"
            ? "/parent/dashboard"
            : "/admin/statistics"
          : "/"}
        class="group flex items-center gap-2 transition-transform hover:scale-105 active:scale-95 md:gap-3"
        aria-label="Attendde Home"
      >
        <!-- Logo: A stylized Shield/Book for Education -->
        <div
          class="bg-primary/10 text-primary flex h-9 w-9 items-center justify-center rounded-lg"
        >
          <Shield class="h-6 w-6" strokeWidth={2.5} />
        </div>
        <span
          class="font-montserrat text-base-content text-lg font-bold tracking-tight md:text-xl"
        >
          Attendde
        </span>
      </a>
    </div>

    <!-- Center: desktop categories (Only if logged in) -->
    <div class="navbar-center hidden md:flex">
      {#if currentUser}
        <ul class="menu menu-horizontal gap-1 px-1 text-sm font-medium">
          {#each navItems as item}
            <li>
              <a
                href={item.href}
                class:active={currentPath.startsWith(item.href)}
                class="hover:text-primary gap-2 px-4 transition-colors"
              >
                {item.label}
              </a>
            </li>
          {/each}
        </ul>
      {/if}
    </div>

    <!-- Right side -->
    <div class="navbar-end gap-2 md:gap-3">
      <!-- Kiosk Mode Quick Link (Only for Admin/Teacher) -->
      {#if currentUser && ["admin", "teacher"].includes(currentUser.role)}
        <a
          href="/attendance"
          target="_blank"
          class="btn btn-ghost btn-circle btn-sm tooltip tooltip-bottom hidden md:flex"
          data-tip="Mở Kiosk Điểm danh"
        >
          <Camera class="text-base-content/70 h-5 w-5" />
        </a>
      {/if}

      <!-- Auth -->
      {#if currentUser}
        <div class="dropdown dropdown-end">
          <button
            type="button"
            tabindex="0"
            class="btn btn-ghost btn-sm hover:bg-base-200 hover:border-base-200 h-10 gap-2 rounded-full border border-transparent px-2 normal-case transition-colors"
          >
            <div
              class="bg-primary text-primary-content flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold shadow-sm"
            >
              {currentUser.first_name[0]}
            </div>
            <div class="hidden flex-col items-start text-xs md:flex">
              <span class="max-w-[12ch] truncate leading-none font-bold">
                {currentUser.first_name}
                {currentUser.last_name}
              </span>
              <span
                class="text-base-content/60 mt-0.5 text-[10px] tracking-wide uppercase"
              >
                {currentUser.role === "teacher"
                  ? "Giáo viên"
                  : currentUser.role}
              </span>
            </div>
            <ChevronDown class="h-3 w-3 opacity-50" />
          </button>

          <ul
            tabindex="-1"
            class="menu menu-sm dropdown-content bg-base-100 ring-base-content/5 z-[1] mt-3 w-64 rounded-xl p-2 shadow-xl ring-1"
          >
            <li
              class="menu-title bg-base-200/50 mb-2 rounded-lg px-4 py-3 opacity-100"
            >
              <div class="flex flex-col gap-1">
                <span class="text-base-content text-sm font-bold">
                  {currentUser.first_name}
                  {currentUser.last_name}
                </span>
                <span class="text-base-content/60 text-xs font-normal">
                  @{currentUser.username}
                </span>
                <span
                  class="mt-1 w-fit rounded border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase {getRoleBadgeClass(
                    currentUser.role,
                  )}"
                >
                  {currentUser.role === "teacher"
                    ? "Giáo viên"
                    : currentUser.role}
                </span>
              </div>
            </li>

            <li>
              <a href="/profile" class="gap-3 py-2.5">
                <User class="h-4 w-4 opacity-70" />
                <span>Hồ sơ cá nhân</span>
              </a>
            </li>

            {#if currentUser.role === "admin"}
              <li>
                <a href="/settings" class="gap-3 py-2.5">
                  <Settings class="h-4 w-4 opacity-70" />
                  <span>Cấu hình hệ thống</span>
                </a>
              </li>
            {/if}

            <div class="divider my-1"></div>

            <li>
              <form action="/login?/logout" method="POST" class="w-full p-0">
                <button
                  type="submit"
                  class="text-error hover:bg-error/10 flex w-full gap-3 px-4 py-2.5 font-medium"
                >
                  <LogOut class="h-4 w-4" />
                  <span>Đăng xuất</span>
                </button>
              </form>
            </li>
          </ul>
        </div>
      {:else}
        <!-- Not Logged In State -->
        <div class="flex items-center gap-2">
          <a
            href="/login"
            class="btn btn-ghost btn-sm h-9 min-h-[36px] font-medium"
          >
            Đăng nhập
          </a>
          <!-- Note: Registration is usually internal, but keeping for demo -->
          <a
            href="/contact"
            class="btn btn-primary btn-sm h-9 min-h-[36px] px-4 font-bold text-white shadow-md"
          >
            Liên hệ Demo
          </a>
        </div>
      {/if}
    </div>
  </div>
{/if}
