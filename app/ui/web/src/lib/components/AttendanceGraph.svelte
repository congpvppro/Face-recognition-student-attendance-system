<script lang="ts">
    import { onMount } from "svelte";
    import { Chart, registerables } from "chart.js";

    let { data } = $props();
    let chartCanvas = $state<HTMLCanvasElement>();
    let chartInstance: Chart | null = null;

    onMount(() => {
        // Register Chart.js components
        Chart.register(...registerables);

        // Create chart when component mounts
        if (data && data.length > 0) {
            createChart();
        }

        // Cleanup on unmount
        return () => {
            if (chartInstance) {
                chartInstance.destroy();
            }
        };
    });

    $effect(() => {
        // Update chart when data changes
        if (data && data.length > 0 && chartCanvas) {
            createChart();
        }
    });

    function createChart() {
        // Guard: ensure canvas element exists
        if (!chartCanvas) return;

        // Destroy existing chart if any
        if (chartInstance) {
            chartInstance.destroy();
        }

        const ctx = chartCanvas.getContext("2d");
        if (!ctx) return;

        // Prepare data for Chart.js
        const labels = data.map((d: any) => {
            const date = new Date(d.date);
            return date.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
            });
        });

        const presentRates = data.map((d: any) => d.present_rate);
        const presentCounts = data.map((d: any) => d.present_count);
        const absentCounts = data.map((d: any) => d.absent_count);

        chartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Attendance Rate (%)",
                        data: presentRates,
                        borderColor: "rgb(59, 130, 246)", // Tailwind blue-500
                        backgroundColor: "rgba(59, 130, 246, 0.1)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: "rgb(59, 130, 246)",
                        pointBorderColor: "#fff",
                        pointBorderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: "top",
                        labels: {
                            font: {
                                size: 12,
                            },
                            usePointStyle: true,
                            padding: 15,
                        },
                    },
                    tooltip: {
                        mode: "index",
                        intersect: false,
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: "bold",
                        },
                        bodyFont: {
                            size: 13,
                        },
                        callbacks: {
                            label: function (context) {
                                const index = context.dataIndex;
                                const rate = presentRates[index];
                                const present = presentCounts[index];
                                const absent = absentCounts[index];
                                const total = present + absent;

                                return [
                                    `Rate: ${rate}%`,
                                    `Present: ${present}/${total}`,
                                    `Absent: ${absent}`,
                                ];
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function (value) {
                                return value + "%";
                            },
                            font: {
                                size: 11,
                            },
                        },
                        grid: {
                            color: "rgba(0, 0, 0, 0.05)",
                        },
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            font: {
                                size: 10,
                            },
                        },
                        grid: {
                            display: false,
                        },
                    },
                },
                interaction: {
                    mode: "nearest",
                    axis: "x",
                    intersect: false,
                },
            },
        });
    }
</script>

```
<div class="w-full">
    {#if data && data.length > 0}
        <div class="relative h-64 md:h-80">
            <canvas bind:this={chartCanvas}></canvas>
        </div>
    {:else}
        <div class="alert alert-info">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                class="stroke-current shrink-0 w-6 h-6"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                ></path>
            </svg>
            <span>No attendance data available for the selected period.</span>
        </div>
    {/if}
</div>
```

<style>
    /* Add custom styles if needed */
</style>
