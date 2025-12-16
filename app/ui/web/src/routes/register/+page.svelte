<script lang="ts">
  import { Lock, Mail, User, Shield } from "lucide-svelte";
  import { enhance } from "$app/forms";
  import { goto } from "$app/navigation";
  import { page } from "$app/state";
  import { showToast } from "$lib/toastStore";

  let submitting = $state(false);
  let password = $state("");
  let confirmPassword = $state("");
  let passwordsMatch = $derived(
    password === confirmPassword && password !== "",
  );

  const namePattern = "[\\p{L}\\s'\\-]+";
  const passwordPattern = ".{6,}";
  let clientError = $state<string | null>(null);

  let touched = $state(new Set<string>());

  let fnameInput: HTMLInputElement;
  let lnameInput: HTMLInputElement;
  let usernameInput: HTMLInputElement;
  let emailInput: HTMLInputElement;
  let passwordInput: HTMLInputElement;
  let confirmPasswordInput: HTMLInputElement;

  $effect(() => {
    if (confirmPasswordInput) {
      if (!passwordsMatch && confirmPassword) {
        confirmPasswordInput.setCustomValidity("Mật khẩu không khớp.");
      } else {
        confirmPasswordInput.setCustomValidity("");
      }
    }
  });

  function validateForm() {
    const fields = [
      fnameInput,
      lnameInput,
      usernameInput,
      emailInput,
      passwordInput,
      confirmPasswordInput,
    ];

    for (const field of fields) {
      if (touched.has(field.name) && !field.checkValidity()) {
        clientError = field.dataset.hint || "This field has an error.";
        return;
      }
    }

    clientError = null;
  }

  function handleBlur(event: FocusEvent) {
    const input = event.target as HTMLInputElement;
    if (input.name) {
      touched.add(input.name);
      validateForm();
    }
  }
</script>

<svelte:head>
  <title>Đăng ký - Attendde</title>
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

      <h1 class="font-josefin text-4xl font-bold">Tạo tài khoản</h1>
      <p class="text-base-content/70 mt-2">
        Hành trình của bạn bắt đầu từ đây.
      </p>

      <form
        class="mt-8 space-y-4"
        method="POST"
        action="?"
        use:enhance={() => {
          submitting = true;
          touched = new Set([
            "firstName",
            "lastName",
            "username",
            "email",
            "password",
            "confirmPassword",
          ]);
          validateForm();

          return ({ result, update }) => {
            submitting = false;
            if (result.type === "success" && result.data?.success) {
              showToast({
                message: "Tạo tài khoản thành công.",
                type: "success",
              });
              goto("/login");
            } else {
              update();
            }
          };
        }}
        oninput={validateForm}
        novalidate
      >
        <div class="flow-row flex gap-4">
          <div class="form-control w-full">
            <input
              type="text"
              id="fname"
              name="firstName"
              class="input input-bordered validator"
              required
              placeholder="Họ"
              pattern={namePattern}
              minlength="1"
              maxlength="50"
              title="Chỉ chứa chữ cái, khoảng trắng, dấu gạch ngang (-), hoặc dấu nháy đơn (')."
              data-hint="Họ phải từ 1 đến 50 ký tự, chỉ chứa chữ cái, khoảng trắng, dấu gạch ngang, hoặc dấu nháy đơn."
              bind:this={fnameInput}
              onblur={handleBlur}
            />
          </div>
          <div class="form-control w-full">
            <input
              type="text"
              id="lname"
              name="lastName"
              class="input input-bordered validator"
              required
              placeholder="Tên"
              pattern={namePattern}
              minlength="1"
              maxlength="50"
              title="Chỉ chứa chữ cái, khoảng trắng, dấu gạch ngang (-), hoặc dấu nháy đơn (')."
              data-hint="Tên phải từ 1 đến 50 ký tự, chỉ chứa chữ cái, khoảng trắng, dấu gạch ngang, hoặc dấu nháy đơn."
              bind:this={lnameInput}
              onblur={handleBlur}
            />
          </div>
        </div>

        <div class="form-control">
          <div class="relative">
            <User
              class="pointer-events-none absolute top-1/2 left-3 z-10 size-5 -translate-y-1/2 transform text-gray-500"
            />
            <input
              type="text"
              id="username"
              name="username"
              class="input input-bordered validator w-full pl-10"
              required
              placeholder="Tên đăng nhập"
              pattern="[A-Za-z0-9][A-Za-z0-9\-]*"
              minlength="5"
              maxlength="30"
              title="Chỉ chứa chữ cái, số hoặc dấu gạch ngang"
              data-hint="Tên đăng nhập phải từ 5 đến 30 ký tự, chỉ chứa chữ cái, số hoặc dấu gạch ngang."
              bind:this={usernameInput}
              onblur={handleBlur}
            />
          </div>
        </div>

        <div
          id="email-field"
          style="view-transition-name: auth-email"
          class="form-control"
        >
          <div class="relative">
            <Mail
              class="pointer-events-none absolute top-1/2 left-3 z-10 size-5 -translate-y-1/2 transform text-gray-500"
            />
            <input
              type="email"
              id="email"
              name="email"
              class="input input-bordered validator w-full pl-10"
              required
              placeholder="Nhập email của bạn"
              data-hint="Phải là địa chỉ email hợp lệ."
              bind:this={emailInput}
              onblur={handleBlur}
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
              class="pointer-events-none absolute top-1/2 left-3 z-10 size-5 -translate-y-1/2 transform text-gray-500"
            />
            <input
              type="password"
              id="password"
              name="password"
              class="input input-bordered validator w-full pl-10"
              required
              placeholder="Mật khẩu"
              pattern={passwordPattern}
              data-hint="Mật khẩu phải có ít nhất 6 ký tự."
              bind:value={password}
              bind:this={passwordInput}
              onblur={handleBlur}
            />
          </div>
        </div>

        <div class="form-control">
          <div class="relative">
            <Lock
              class="pointer-events-none absolute top-1/2 left-3 z-10 size-5 -translate-y-1/2 transform text-gray-500"
            />
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              class="input input-bordered validator w-full pl-10"
              required
              placeholder="Xác nhận mật khẩu"
              data-hint="Mật khẩu không khớp."
              bind:value={confirmPassword}
              bind:this={confirmPasswordInput}
              onblur={handleBlur}
            />
          </div>
        </div>

        <div class="relative h-full min-h-[2.5em] md:min-h-[1.5em]">
          <div
            class="text-error absolute left-0 w-fit text-sm transition-opacity duration-100 ease-in-out"
            style="opacity: {clientError ? 1 : 0};"
            aria-live="polite"
            role="status"
          >
            {clientError}
          </div>
          <div
            class="text-error absolute left-0 h-fit w-fit text-sm transition-opacity duration-100 ease-in-out"
            style="opacity: {!clientError && page.form?.message ? 1 : 0};"
            aria-live="polite"
            role="status"
          >
            {page.form?.message}
          </div>
        </div>

        <div class="form-control pt-2 text-center md:text-left">
          <button
            type="submit"
            class="btn btn-primary px-6"
            disabled={submitting || !passwordsMatch || clientError != null}
            style="view-transition-name: auth-submit"
          >
            {#if submitting}
              <span class="loading loading-spinner"></span>
              Đang đăng ký...
            {:else}
              Đăng ký
            {/if}
          </button>
        </div>
      </form>
      <div class="mt-4 text-sm">
        Đã có tài khoản?
        <a href="/login" class="link-primary link">Đăng nhập</a>
      </div>
    </div>
  </div>

  <div
    class="hidden h-full items-center justify-center overflow-visible p-5 pr-0 lg:flex lg:translate-x-20"
  >
    <enhanced:img
      src="$lib/assets/backgrounds/signup_background.jpg"
      class="h-[70vh] max-h-[70vh] min-h-[70svh] w-auto max-w-none rounded-xl object-cover shadow-xl"
      alt="Sign Up Background"
    >
    </enhanced:img>
  </div>
</div>
