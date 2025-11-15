<script lang="ts">
	import { Lock, Mail, User } from "lucide-svelte";
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
				confirmPasswordInput.setCustomValidity(
					"Passwords do not match.",
				);
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

<div class="grid min-h-screen w-full overflow-x-hidden lg:grid-cols-[2fr_3fr]">
	<div
		class="bg-base-100 flex flex-col items-center justify-center p-6 sm:p-8"
	>
		<div class="w-full max-w-md px-6">
			<a
				href="/"
				class="mb-8 flex items-center gap-3 self-start"
				style="view-transition-name: brand-logo"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="50"
					height="50"
					viewBox="0 0 100 100"
				>
					<g fill-rule="evenodd">
						<path fill="#282828" d="M46 12 15 88q-30-38 31-76Z" />
						<path fill="#825F41" d="m54 12 31 76q30-38-31-76Z" />
					</g>
				</svg>
				<span class="text-2xl font-bold">L'Artelier</span>
			</a>

			<h1 class="font-josefin text-4xl font-bold">Create an account</h1>
			<p class="text-base-content/70 mt-2">Your journey begins here.</p>

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
								message: "Account created successfully.",
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
							placeholder="First name"
							pattern={namePattern}
							minlength="1"
							maxlength="50"
							title="Only letters, spaces, hyphens (-), or apostrophes (')."
							data-hint="First name must be 1 to 50 characters, containing only letters, spaces, hyphens, or apostrophes."
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
							placeholder="Last name"
							pattern={namePattern}
							minlength="1"
							maxlength="50"
							title="Only letters, spaces, hyphens (-), or apostrophes (')."
							data-hint="Last name must be 1 to 50 characters, containing only letters, spaces, hyphens, or apostrophes."
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
							placeholder="Username"
							pattern="[A-Za-z0-9][A-Za-z0-9\-]*"
							minlength="5"
							maxlength="30"
							title="Only letters, numbers or dash"
							data-hint="Username must be 5 to 30 characters, containing only letters, numbers or a dash."
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
							placeholder="Enter your email"
							data-hint="Must be a valid email address."
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
							placeholder="Password"
							pattern={passwordPattern}
							data-hint="Password must be at least 6 characters."
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
							placeholder="Confirm password"
							data-hint="Passwords do not match."
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
						style="opacity: {!clientError && page.form?.message
							? 1
							: 0};"
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
						disabled={submitting ||
							!passwordsMatch ||
							clientError != null}
						style="view-transition-name: auth-submit"
					>
						{#if submitting}
							<span class="loading loading-spinner"></span>
							Signing Up...
						{:else}
							Sign Up
						{/if}
					</button>
				</div>
			</form>
			<div class="mt-4 text-sm">
				Already have an account?
				<a href="/login" class="link-primary link">Login</a>
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
