<script lang="ts">
  import type { LayoutProps } from "./$types";

  let { children }: LayoutProps = $props();
</script>

<div class="">
  <main class="">
    {@render children()}
  </main>
</div>
