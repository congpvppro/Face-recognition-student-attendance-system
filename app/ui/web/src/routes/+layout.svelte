<script lang="ts">
  import "../app.css";
  import "@fontsource-variable/josefin-sans";
  import "@fontsource-variable/raleway";
  import "@fontsource-variable/work-sans";
  import "@fontsource/cormorant-sc";
  import "@fontsource-variable/montserrat";

  import { onMount } from "svelte";
  import { Spring } from "svelte/motion";
  import { browser } from "$app/environment";
  import { page } from "$app/state";

  //   import favicon from "$lib/assets/favicon.png";
  import Footer from "$lib/components/Footer.svelte";
  import ToastContainer from "$lib/components/ToastContainer.svelte";
  import NavigationBar from "$lib/components/NavigationBar.svelte";
  import type { LayoutProps } from "./$types";

  let { children, data }: LayoutProps = $props();

  $effect(() => {
    console.log("Layout Data:", data);
    console.log("Layout Data User:", data?.user);
  });

  // Constants
  const INTERACTIVE_SELECTOR =
    'a, button, input, textarea, select, label, [role="button"], [role="link"], [tabindex]:not([tabindex="-1"]), .cursor-pointer';

  // Cursor State
  const mouse = new Spring(
    { x: 0, y: 0 },
    {
      stiffness: 0.35,
      damping: 0.8,
      precision: 0.5,
    },
  );

  let showCursor = $state(false);
  let cursorDown = $state(false);
  let overInteractive = $state(false);
  let isPageVisible = $state(true);
  let cursorEl: HTMLDivElement | null = $state(null);

  let rafId: number | null = null;
  let pendingX = 0;
  let pendingY = 0;
  let pendingTarget: EventTarget | null = null;
  let lastInteractiveCheck = 0;
  const INTERACTIVE_CHECK_INTERVAL = 50;

  // Cache for interactive element detection
  let cachedElement: Element | null = null;
  let cachedResult = false;

  // Interactive Element Detection
  function checkInteractive(target: EventTarget | null): boolean {
    if (!target || !(target instanceof Element)) return false;

    const interactiveParent = target.closest(INTERACTIVE_SELECTOR);

    if (interactiveParent === cachedElement) {
      return cachedResult;
    }

    cachedElement = interactiveParent;
    cachedResult = interactiveParent !== null;
    return cachedResult;
  }

  // Batched cursor update - runs once per animation frame
  function flushCursorUpdate() {
    rafId = null;

    // Update spring target
    mouse.target = { x: pendingX, y: pendingY };

    const now = performance.now();
    if (now - lastInteractiveCheck >= INTERACTIVE_CHECK_INTERVAL) {
      lastInteractiveCheck = now;
      const newInteractive = checkInteractive(pendingTarget);
      // Only update state if changed
      if (newInteractive !== overInteractive) {
        overInteractive = newInteractive;
      }
    }
  }

  // Event Handlers
  function handleMouseMove(event: MouseEvent) {
    if (!isPageVisible) return;

    pendingX = event.clientX;
    pendingY = event.clientY;
    pendingTarget = event.target;

    if (rafId === null) {
      rafId = requestAnimationFrame(flushCursorUpdate);
    }

    if (!showCursor) showCursor = true;
  }

  function handleMouseLeave() {
    showCursor = false;
    overInteractive = false;
    cachedElement = null;
    // Cancel pending RAF
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  function handleMouseEnter() {
    showCursor = true;
  }

  function handleMouseDown() {
    cursorDown = true;
  }

  function handleMouseUp() {
    cursorDown = false;
  }

  function handleVisibilityChange() {
    isPageVisible = !document.hidden;
    if (document.hidden && rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  $effect(() => {
    if (!cursorEl) return;

    const x = mouse.current.x;
    const y = mouse.current.y;

    // Direct DOM manipulation
    cursorEl.style.setProperty("--cursor-x", `${x}px`);
    cursorEl.style.setProperty("--cursor-y", `${y}px`);
  });

  // Lifecycle
  onMount(() => {
    if (!browser) return;

    const setHeaderHeight = () => {
      const nav = document.querySelector(".navbar");
      const height = nav ? nav.getBoundingClientRect().height : 0;
      document.documentElement.style.setProperty(
        "--header-height",
        `${height}px`,
      );
    };

    setHeaderHeight();
    const ro = new ResizeObserver(setHeaderHeight);
    const navEl = document.querySelector(".navbar");
    if (navEl) ro.observe(navEl);

    // Platform detection
    if (navigator.userAgent.includes("Firefox")) {
      document.documentElement.classList.add("platform-firefox");
    }

    // Custom cursor detection (pointer: fine = mouse/trackpad)
    const hasFineCursor = window.matchMedia("(pointer: fine)").matches;
    if (hasFineCursor) {
      showCursor = true;
      document.documentElement.classList.add("has-custom-cursor");
    }

    // Visibility change listener
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      ro.disconnect();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
    };
  });

  // Derived State
  const isAuthPage = $derived(
    ["/login", "/register"].includes(page.url.pathname),
  );
</script>

<svelte:head>
  <!-- <link rel="icon" href={favicon} /> -->
</svelte:head>

<svelte:window
  onmousemove={handleMouseMove}
  onmouseleave={handleMouseLeave}
  onmouseenter={handleMouseEnter}
  onmousedown={handleMouseDown}
  onmouseup={handleMouseUp}
/>

<ToastContainer />

{#if showCursor}
  <div
    bind:this={cursorEl}
    class="circle-cursor"
    class:is-down={cursorDown}
    class:is-interactive={overInteractive}
    aria-hidden="true"
  ></div>
{/if}

<main
  class="flex flex-col overflow-hidden"
  class:h-dvh={page.url.pathname === "/"}
  style:padding-top={isAuthPage ? "0px" : "var(--header-height, 0px)"}
>
  {#if !isAuthPage}
    <NavigationBar user={data.user} />
  {/if}

  <div class=" overflow-x-hidden h-dvh overflow-y-auto scroll-smooth">
    {@render children()}
  </div>
  <Footer />
</main>

<style>
  main {
    padding-top: var(--header-height, 0px);
  }

  :global(html.has-custom-cursor),
  :global(html.has-custom-cursor body) {
    cursor:
      url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="white"/></svg>')
        4 4,
      auto;
  }

  :global(html.has-custom-cursor a),
  :global(html.has-custom-cursor button),
  :global(html.has-custom-cursor [role="button"]),
  :global(html.has-custom-cursor input[type="button"]),
  :global(html.has-custom-cursor input[type="submit"]),
  :global(html.has-custom-cursor input[type="reset"]) {
    cursor:
      url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="white"/></svg>')
        4 4,
      pointer;
  }

  .circle-cursor {
    --cursor-x: 0px;
    --cursor-y: 0px;

    position: fixed;
    top: 0;
    left: 0;
    z-index: 9999;

    transform: translate3d(var(--cursor-x), var(--cursor-y), 0)
      translate(-50%, -50%);

    /* Size */
    width: 32px;
    height: 32px;

    /* Shape */
    border-radius: 50%;
    border: 2px solid white;
    background-color: transparent;

    /* Interaction */
    pointer-events: none;
    user-select: none;

    /* Blend mode */
    mix-blend-mode: difference;

    /* GPU acceleration */
    will-change: transform;
    backface-visibility: hidden;

    contain: layout style paint size;

    /* Shadow effect */
    filter: drop-shadow(0 0 2px rgba(255, 255, 255, 0.5));

    transition:
      width 180ms cubic-bezier(0.4, 0, 0.2, 1),
      height 180ms cubic-bezier(0.4, 0, 0.2, 1),
      border-width 180ms cubic-bezier(0.4, 0, 0.2, 1),
      background-color 180ms cubic-bezier(0.4, 0, 0.2, 1),
      filter 180ms cubic-bezier(0.4, 0, 0.2, 1),
      opacity 200ms ease-out;
  }

  .circle-cursor.is-down {
    width: 42px;
    height: 42px;
    border-width: 2.5px;
    filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.6));
  }

  .circle-cursor.is-interactive {
    width: 40px;
    height: 40px;
    border-width: 2.5px;
    background-color: rgba(255, 255, 255, 0.15);
    filter: drop-shadow(0 0 2.5px rgba(255, 255, 255, 0.55));
  }

  .circle-cursor.is-interactive.is-down {
    width: 48px;
    height: 48px;
    border-width: 3px;
    background-color: rgba(255, 255, 255, 0.2);
    filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.65));
  }

  @media (prefers-reduced-motion: reduce) {
    .circle-cursor {
      transition: none;
    }
  }

  @media (pointer: coarse) {
    .circle-cursor {
      display: none !important;
    }
  }
</style>
