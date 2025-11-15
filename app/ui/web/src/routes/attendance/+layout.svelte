<script lang="ts">
    import type { LayoutProps } from "./$types";

    let { children }: LayoutProps = $props();
</script>

<main class="bg-base-200 min-h-screen min-w-full">
    {@render children()}
</main>
