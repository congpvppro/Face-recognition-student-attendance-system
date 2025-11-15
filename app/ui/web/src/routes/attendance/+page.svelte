<script lang="ts">
    import { onMount } from "svelte";
    import { showToast } from "$lib/toastStore";

    type ClassData = {
        id: number;
        name: string;
    };

    let { data }: { data: { classes: ClassData[] } } = $props();

    let videoElement: HTMLVideoElement;
    let canvasElement: HTMLCanvasElement;

    let mode = $state<"attendance" | "registration">("attendance");
    let isProcessing = $state(false);
    let statusMessage = $state("Initializing...");
    let errorMessage = $state("");
    let selectedClassId = $state<number | null>(null);
    let cameraSupported = $state(true);

    let recognizedStudentId = $state<string | null>(null);
    let lastRecognitionTime = $state(0);
    const recognitionCooldown = 5000;

    let stream: MediaStream | null = $state(null);
    let recognitionInterval: number | undefined;
    let isCameraReady = $state(false);

    let canCapture = $derived(isCameraReady && !isProcessing);
    let shouldShowRecognitionOverlay = $derived(
        recognizedStudentId !== null && mode === "attendance",
    );

    onMount(() => {
        setupCamera();

        const checkAndRecognize = () => {
            if (mode === "attendance" && canCapture) {
                startRecognition();
            }
        };

        recognitionInterval = window.setInterval(checkAndRecognize, 2000);

        return () => {
            if (recognitionInterval) clearInterval(recognitionInterval);
            stopCamera();
        };
    });

    $effect(() => {
        statusMessage =
            mode === "attendance"
                ? "Camera ready."
                : "Select a class and register your face.";
        errorMessage = "";
        recognizedStudentId = null;

        return () => {};
    });

    async function setupCamera() {
        if (stream || !videoElement) return;

        if (
            typeof navigator !== "undefined" &&
            navigator.mediaDevices?.getUserMedia
        ) {
            try {
                const constraints: MediaStreamConstraints = {
                    video: {
                        width: { ideal: 1280, max: 1920 },
                        height: { ideal: 720, max: 1080 },
                        aspectRatio: { ideal: 16 / 9 },
                        facingMode: { ideal: "user" },
                        frameRate: { ideal: 30 },
                    },
                    audio: false,
                };

                stream = await navigator.mediaDevices.getUserMedia(constraints);
                videoElement.srcObject = stream;

                await videoElement.play();

                isCameraReady = true;
                statusMessage = "Camera ready.";
                cameraSupported = true;
                errorMessage = "";
            } catch (err: any) {
                console.error("Error accessing camera:", err);

                let message = "Could not access the camera.";
                if (err.name === "NotAllowedError") {
                    message =
                        "Camera permission denied. Please allow camera access.";
                } else if (err.name === "NotFoundError") {
                    message = "No camera found on this device.";
                } else if (err.name === "NotReadableError") {
                    message =
                        "Camera is already in use by another application.";
                }

                errorMessage = message;
                statusMessage = "Camera error";
                cameraSupported = false;
                isCameraReady = false;
            }
        } else {
            errorMessage = "Media devices are not supported in this browser.";
            statusMessage = "Unsupported browser";
            cameraSupported = false;
            isCameraReady = false;
        }
    }

    function stopCamera() {
        stream?.getTracks().forEach((track) => track.stop());
        stream = null;

        if (videoElement) {
            videoElement.srcObject = null;
        }

        isCameraReady = false;
    }

    async function captureFrameToBlob(): Promise<Blob | null> {
        if (
            !videoElement ||
            !canvasElement ||
            videoElement.paused ||
            videoElement.ended ||
            !isCameraReady
        ) {
            return null;
        }

        const context = canvasElement.getContext("2d", {
            willReadFrequently: false,
        });
        if (!context) return null;

        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;

        context.save();
        context.scale(-1, 1);
        context.drawImage(
            videoElement,
            -canvasElement.width,
            0,
            canvasElement.width,
            canvasElement.height,
        );
        context.restore();

        return await new Promise((resolve) =>
            canvasElement.toBlob((blob) => resolve(blob), "image/jpeg", 0.92),
        );
    }

    async function sendBlob(
        blob: Blob,
        endpoint: string,
        onOk: (result: any) => void,
    ) {
        const formData = new FormData();
        formData.append("image", blob, "capture.jpg");

        if (mode === "registration" && selectedClassId !== null) {
            formData.append("classId", selectedClassId.toString());
        } else if (mode === "attendance") {
            formData.append("classId", "1");
        }

        const response = await fetch(endpoint, {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            onOk(result);
        } else {
            const errorResult = await response.json().catch(() => null);
            const errorMsg =
                errorResult?.detail ||
                errorResult?.message ||
                "Request failed.";
            statusMessage = `Error: ${errorMsg}`;

            showToast({
                message: errorMsg,
                type: "error",
            });
        }
    }

    async function captureAndProcess(
        endpoint: string,
        onOk: (result: any) => void,
    ) {
        if (isProcessing || !isCameraReady) return;

        isProcessing = true;
        statusMessage = "Processing...";
        errorMessage = "";

        try {
            const blob = await captureFrameToBlob();
            if (!blob) {
                statusMessage = "Failed to capture image. Please try again.";
                return;
            }
            await sendBlob(blob, endpoint, onOk);
        } catch (err) {
            console.error("Request failed:", err);
            statusMessage = "Network error. Could not connect to the server.";
            showToast({
                message: "Network error occurred",
                type: "error",
            });
        } finally {
            isProcessing = false;
        }
    }

    async function handleFileCapture(event: Event) {
        if (isProcessing) return;

        const input = event.currentTarget as HTMLInputElement;
        const file = input.files?.[0];
        if (!file) return;

        isProcessing = true;
        statusMessage = "Processing captured image...";
        errorMessage = "";

        try {
            const endpoint =
                mode === "registration"
                    ? "/api/students/register-face"
                    : "/api/attendance/recognize";

            await sendBlob(
                file,
                endpoint,
                mode === "registration"
                    ? handleRegistration
                    : handleRecognition,
            );
        } catch (err) {
            console.error("Request failed:", err);
            statusMessage = "Network error. Could not connect to the server.";
        } finally {
            isProcessing = false;
            input.value = "";
        }
    }

    function handleRecognition(result: any) {
        recognizedStudentId = result.student_id;
        statusMessage = `Welcome, Student ${recognizedStudentId}!`;
        lastRecognitionTime = Date.now();

        showToast({
            message: `Attendance recorded for ${recognizedStudentId}`,
            type: "success",
        });

        setTimeout(() => {
            if (Date.now() - lastRecognitionTime >= recognitionCooldown) {
                statusMessage = "Camera ready.";
                recognizedStudentId = null;
            }
        }, recognitionCooldown);
    }

    function handleRegistration(result: any) {
        statusMessage = `Face registered with ID: ${result.face_id}`;
        showToast({
            message: "Face registered successfully!",
            type: "success",
        });

        setTimeout(() => {
            statusMessage = "Camera ready.";
        }, 3000);
    }

    function startRecognition() {
        if (
            mode === "attendance" &&
            canCapture &&
            Date.now() - lastRecognitionTime >= recognitionCooldown
        ) {
            captureAndProcess("/api/attendance/recognize", handleRecognition);
        }
    }

    function switchMode(newMode: "attendance" | "registration") {
        if (mode === newMode) return;

        mode = newMode;
        recognizedStudentId = null;
        errorMessage = "";
    }
</script>

<div class="flex min-h-screen flex-col items-center justify-center p-4">
    <div class="card w-full max-w-3xl bg-base-100 shadow-xl">
        <div class="card-body gap-4">
            <div
                class="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center"
            >
                <div>
                    <h1 class="card-title text-3xl">
                        {mode === "attendance"
                            ? "Attendance Kiosk"
                            : "Registration Kiosk"}
                    </h1>
                    <p class="mt-1 text-sm opacity-70">
                        Look at the camera and hold still while your face is
                        processed.
                    </p>
                </div>

                <div class="join">
                    <button
                        class="btn btn-sm join-item"
                        class:btn-primary={mode === "attendance"}
                        class:btn-ghost={mode !== "attendance"}
                        onclick={() => switchMode("attendance")}
                    >
                        Attendance
                    </button>
                    <button
                        class="btn btn-sm join-item"
                        class:btn-primary={mode === "registration"}
                        class:btn-ghost={mode !== "registration"}
                        onclick={() => switchMode("registration")}
                    >
                        Registration
                    </button>
                </div>
            </div>

            <div class="divider"></div>

            <div
                class="relative mx-auto w-full max-w-2xl overflow-hidden rounded-lg bg-black"
                style="aspect-ratio: 16/9;"
            >
                <video
                    bind:this={videoElement}
                    autoplay
                    muted
                    playsinline
                    disablepictureinpicture
                    class="h-full w-full object-cover"
                ></video>

                {#if !isCameraReady && cameraSupported}
                    <div
                        class="absolute inset-0 flex items-center justify-center bg-black/60"
                    >
                        <span
                            class="loading loading-dots loading-lg text-primary"
                        ></span>
                    </div>
                {/if}

                {#if shouldShowRecognitionOverlay}
                    <div
                        class="absolute inset-0 flex items-center justify-center bg-black/50"
                    >
                        <div
                            class="scale-105 transform rounded-lg bg-green-500/90 p-8 text-center text-white shadow-2xl"
                        >
                            <svg
                                class="mx-auto mb-2 h-16 w-16"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                            <h2 class="text-3xl font-bold">Welcome!</h2>
                            <p class="mt-2 text-2xl">{recognizedStudentId}</p>
                        </div>
                    </div>
                {/if}
            </div>

            <div class="mt-2 flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                    <span
                        class="h-2 w-2 rounded-full transition-colors"
                        class:bg-green-500={isCameraReady}
                        class:bg-red-500={!isCameraReady}
                        class:animate-pulse={!isCameraReady && cameraSupported}
                    ></span>
                    {#if errorMessage}
                        <p class="text-sm text-error">
                            {errorMessage}
                        </p>
                    {:else}
                        <p class="text-sm">
                            {statusMessage}
                        </p>
                    {/if}
                </div>

                {#if isProcessing}
                    <span
                        class="loading loading-spinner loading-sm text-primary"
                    ></span>
                {/if}
            </div>

            {#if mode === "registration"}
                <div class="mx-auto mt-4 w-full max-w-sm space-y-4">
                    <div class="form-control">
                        <label for="classId" class="label">
                            <span class="label-text font-medium"
                                >Select class</span
                            >
                        </label>
                        <select
                            bind:value={selectedClassId}
                            id="classId"
                            class="select select-bordered"
                            required
                        >
                            <option disabled selected value={null}>
                                -- Select a class --
                            </option>
                            {#each data.classes as cls}
                                <option value={cls.id}>{cls.name}</option>
                            {/each}
                        </select>
                    </div>

                    <button
                        class="btn btn-primary w-full"
                        onclick={() =>
                            captureAndProcess(
                                "/api/students/register-face",
                                handleRegistration,
                            )}
                        disabled={selectedClassId === null || !canCapture}
                    >
                        {#if isProcessing}
                            <span class="loading loading-spinner loading-sm"
                            ></span>
                            Registering...
                        {:else}
                            Register Face
                        {/if}
                    </button>
                </div>
            {/if}

            {#if !cameraSupported}
                <div class="alert alert-warning mx-auto mt-4 max-w-sm">
                    <svg
                        class="h-6 w-6 flex-shrink-0"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                    </svg>
                    <div class="flex-1">
                        <p class="text-sm">
                            Camera access unavailable. Use your device camera to
                            capture an image.
                        </p>
                        <label class="btn btn-outline btn-sm mt-2 w-full">
                            <svg
                                class="h-4 w-4"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                                />
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                                />
                            </svg>
                            Capture Photo
                            <input
                                type="file"
                                accept="image/*"
                                capture="user"
                                class="hidden"
                                onchange={handleFileCapture}
                            />
                        </label>
                    </div>
                </div>
            {/if}
        </div>
    </div>
</div>

<canvas bind:this={canvasElement} class="hidden" aria-hidden="true"></canvas>

<style>
    video {
        transform: scaleX(-1);
    }
</style>
