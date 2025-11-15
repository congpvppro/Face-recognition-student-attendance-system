<script>
	let { data } = $props();
</script>

<svelte:head>
	<title>Your Profile</title>
</svelte:head>

<div class="profile-container">
	<h1>Your Profile</h1>

	{#if data.user}
		<div class="user-details">
			<p><strong>Username:</strong> {data.user.username}</p>
			<p><strong>Email:</strong> {data.user.email}</p>
			<p><strong>Name:</strong> {data.user.first_name} {data.user.last_name}</p>
			<p><strong>Role:</strong> {data.user.role}</p>
		</div>
	{:else}
		<p>Loading user data or you are not logged in.</p>
	{/if}
</div>

<style>
	.profile-container {
		max-width: 600px;
		margin: 2rem auto;
		padding: 2rem;
		border: 1px solid #ccc;
		border-radius: 8px;
	}
	.user-details p {
		margin: 0.5rem 0;
	}
</style>
