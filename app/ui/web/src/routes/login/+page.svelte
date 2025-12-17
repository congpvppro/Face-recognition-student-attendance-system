<script lang="ts">
  import { Lock, Mail, Shield } from "lucide-svelte";
  import { enhance } from "$app/forms";
  import { goto } from "$app/navigation";
  import { page } from "$app/state";
  import { showToast } from "$lib/toastStore";

  let submitting = $state(false);
</script>

<svelte:head>
  <title>Đăng nhập - Attendde</title>
</svelte:head>

<div class="grid min-h-screen w-full overflow-x-hidden lg:grid-cols-[2fr_3fr]">
  <div class="bg-base-100 flex flex-col items-center justify-center p-6 sm:p-8">
    <div class="w-full max-w-md px-6">
      <a
        href="/"
        class="mb-8 flex items-center gap-3 self-start transition-transform hover:scale-105 active:scale-95"
        style="view-transition-name: brand-logo"
      >
        <div
          class="bg-primary/10 text-primary flex h-11 w-11 items-center justify-center rounded-lg"
        >
          <Shield class="h-7 w-7" strokeWidth={2.5} />
        </div>
        <span class="font-montserrat text-2xl font-bold tracking-tight"
          >Attendde</span
        >
      </a>

      <h1 class="font-josefin text-4xl font-bold">Chào mừng trở lại</h1>
      <p class="text-base-content/70 mt-2">Đăng nhập để tiếp tục.</p>

      <form
        class="mt-8 space-y-4"
        method="POST"
        action="?/login"
        use:enhance={() => {
          submitting = true;

          return async ({ result, update }) => {
            if (result.type === "redirect") {
              showToast({ message: "Đăng nhập thành công!", type: "success" });
              await update(); // lets SvelteKit follow the redirect
            } else if (result.type === "failure") {
              await update(); // show validation/message in page.form
            } else {
              await update(); // handle "success"/"error" consistently
            }

            submitting = false;
          };
        }}
      >
        <div
          id="email-field"
          style="view-transition-name: auth-email"
          class="form-control"
        >
          <div class="relative">
            <Mail
              class="pointer-events-none absolute top-1/2 left-3 z-10 size-5 -translate-y-1/2 transform text-gray-600"
            />
            <input
              type="email"
              id="email"
              name="email"
              class="input input-bordered w-full pl-10"
              required
              placeholder="Nhập email của bạn"
            />
          </div>
        </div>

        <div
          id="password-field"
          class="form-control"
          style="view-transition-name: auth-password"
        >
          <div class="relative">
            <Lock
              class="pointer-events-none absolute top-1/2 left-3 z-10 size-5 -translate-y-1/2 transform text-gray-600"
            />
            <input
              type="password"
              id="password"
              name="password"
              class="input input-bordered w-full pl-10"
              required
              placeholder="Mật khẩu"
            />
          </div>
        </div>

        {#if page.form?.message}
          <div class="text-error min-h-[1rem] w-fit text-sm">
            {page.form.message}
          </div>
        {:else}
          <div class="min-h-[1rem]"></div>
        {/if}

        <div class="form-control pt-2">
          <button
            type="submit"
            class="btn btn-primary px-6"
            disabled={submitting}
            style="view-transition-name: auth-submit"
          >
            {#if submitting}
              <span class="loading loading-spinner"></span>
              Đang đăng nhập...
            {:else}
              Đăng nhập
            {/if}
          </button>
        </div>

        <div class="text-sm">
          Chưa có tài khoản?
          <a href="/register" class="link-primary link">Đăng ký</a>
        </div>
      </form>
    </div>
  </div>

  <div
    class="hidden h-full items-center justify-center overflow-visible p-5 pr-0 lg:flex lg:translate-x-20"
  >
    <enhanced:img
      src="$lib/assets/backgrounds/signin_background.jpg"
      class="h-[70vh] max-h-[70vh] w-auto max-w-none rounded-xl object-cover shadow-xl"
      alt="Login Background"
    >
    </enhanced:img>
  </div>
</div>
