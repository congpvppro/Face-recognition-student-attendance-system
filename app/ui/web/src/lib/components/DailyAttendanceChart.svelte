<script lang="ts">
    import { onMount } from "svelte";
    import Chart from "chart.js/auto";

    let { data } = $props();
    let chartCanvas = $state<HTMLCanvasElement | undefined>();
    let chart = $state<Chart | undefined>();

    $effect(() => {
        if (!chartCanvas || !data) return;

        // Destroy existing chart
        if (chart) {
            chart.destroy();
        }

        // Create new chart
        chart = new Chart(chartCanvas, {
            type: "pie",
            data: {
                labels: ["Có mặt đúng giờ", "Đi muộn", "Vắng"],
                datasets: [
                    {
                        data: [
                            data.on_time || 0,
                            data.late || 0,
                            data.absent || 0,
                        ],
                        backgroundColor: [
                            "rgb(34, 197, 94)", // green - on time
                            "rgb(251, 191, 36)", // yellow - late
                            "rgb(239, 68, 68)", // red - absent
                        ],
                        borderWidth: 2,
                        borderColor: "#fff",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            padding: 15,
                            font: {
                                size: 12,
                            },
                        },
                    },
                    title: {
                        display: true,
                        text: `Điểm danh ngày ${data.date}`,
                        font: {
                            size: 16,
                            weight: "bold",
                        },
                        padding: {
                            top: 10,
                            bottom: 20,
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context: any) {
                                const label = context.label || "";
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce(
                                    (a: number, b: number) => a + b,
                                    0,
                                );
                                const percentage =
                                    total > 0
                                        ? ((value / total) * 100).toFixed(1)
                                        : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            },
                        },
                    },
                },
            },
        });

        return () => {
            if (chart) {
                chart.destroy();
            }
        };
    });
</script>

<div class="w-full h-[300px]">
    <canvas bind:this={chartCanvas}></canvas>
</div>
