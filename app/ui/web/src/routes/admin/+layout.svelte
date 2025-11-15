<script lang="ts">
    import AdminNavigationBar from "$lib/components/AdminNavigationBar.svelte";
    import type { LayoutProps } from "./$types";

    let { children }: LayoutProps = $props();
</script>

<div class="">
    <AdminNavigationBar />
    <main class="">
        {@render children()}
    </main>
</div>
