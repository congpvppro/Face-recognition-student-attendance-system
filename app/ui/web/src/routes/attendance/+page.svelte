<script lang="ts">
  import { onMount } from "svelte";
  import { showToast } from "$lib/toastStore";
  import {
    Camera,
    CameraOff,
    CheckCircle,
    School,
    UserPlus,
    ScanFace,
    Loader2,
    AlertTriangle,
    RefreshCw,
  } from "lucide-svelte";

  type ClassData = {
    id: number;
    name: string;
  };

  let { data }: { data: { classes: ClassData[] } } = $props();

  let videoElement: HTMLVideoElement;
  let canvasElement: HTMLCanvasElement;

  let mode = $state<"attendance" | "registration">("attendance");
  let isProcessing = $state(false);
  let statusMessage = $state("Đang khởi tạo...");
  let errorMessage = $state("");
  let selectedClassId = $state<number | null>(null);
  let cameraSupported = $state(true);

  let recognizedStudentId = $state<string | null>(null);
  let recognizedStudentName = $state<string | null>(null);
  let lastRecognitionTime = $state(0);
  const recognitionCooldown = 5000;

  let stream: MediaStream | null = $state(null);
  let recognitionInterval: number | undefined;
  let isCameraReady = $state(false);

  let canCapture = $derived(isCameraReady && !isProcessing);
  let shouldShowRecognitionOverlay = $derived(
    recognizedStudentId !== null && mode === "attendance",
  );

  // Current time for display
  let currentTime = $state(new Date());
  let timeInterval: number | undefined;

  onMount(() => {
    setupCamera();

    const checkAndRecognize = () => {
      if (mode === "attendance" && canCapture) {
        startRecognition();
      }
    };

    recognitionInterval = window.setInterval(checkAndRecognize, 2000);

    // Update time every second
    timeInterval = window.setInterval(() => {
      currentTime = new Date();
    }, 1000);

    return () => {
      if (recognitionInterval) clearInterval(recognitionInterval);
      if (timeInterval) clearInterval(timeInterval);
      stopCamera();
    };
  });

  $effect(() => {
    statusMessage =
      mode === "attendance"
        ? "Đang chờ nhận diện khuôn mặt..."
        : "Chọn lớp và đăng ký khuôn mặt học sinh mới.";
    errorMessage = "";
    recognizedStudentId = null;
    recognizedStudentName = null;

    return () => {};
  });

  // Format time for display
  function formatTime(date: Date): string {
    return date.toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  function formatDate(date: Date): string {
    return date.toLocaleDateString("vi-VN", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

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
        statusMessage = "Camera sẵn sàng.";
        cameraSupported = true;
        errorMessage = "";
      } catch (err: any) {
        console.error("Error accessing camera:", err);

        let message = "Không thể truy cập camera.";
        if (err.name === "NotAllowedError") {
          message =
            "Quyền truy cập camera bị từ chối. Vui lòng cho phép truy cập camera.";
        } else if (err.name === "NotFoundError") {
          message = "Không tìm thấy camera trên thiết bị này.";
        } else if (err.name === "NotReadableError") {
          message = "Camera đang được sử dụng bởi ứng dụng khác.";
        }

        errorMessage = message;
        statusMessage = "Lỗi camera";
        cameraSupported = false;
        isCameraReady = false;
      }
    } else {
      errorMessage = "Trình duyệt không hỗ trợ thiết bị media.";
      statusMessage = "Trình duyệt không hỗ trợ";
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
        errorResult?.detail || errorResult?.message || "Request failed.";
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
    statusMessage = "Đang xử lý...";
    errorMessage = "";

    try {
      const blob = await captureFrameToBlob();
      if (!blob) {
        statusMessage = "Không thể chụp ảnh. Vui lòng thử lại.";
        return;
      }
      await sendBlob(blob, endpoint, onOk);
    } catch (err) {
      console.error("Request failed:", err);
      statusMessage = "Lỗi mạng. Không thể kết nối đến máy chủ.";
      showToast({
        message: "Đã xảy ra lỗi mạng",
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
    statusMessage = "Đang xử lý ảnh đã chụp...";
    errorMessage = "";

    try {
      const endpoint =
        mode === "registration"
          ? "/api/students/register-face"
          : "/api/attendance/recognize";

      await sendBlob(
        file,
        endpoint,
        mode === "registration" ? handleRegistration : handleRecognition,
      );
    } catch (err) {
      console.error("Request failed:", err);
      statusMessage = "Lỗi mạng. Không thể kết nối đến máy chủ.";
    } finally {
      isProcessing = false;
      input.value = "";
    }
  }

  function handleRecognition(result: any) {
    recognizedStudentId = result.student_id;
    recognizedStudentName = result.student_name || result.student_id;
    statusMessage = `Xin chào, ${recognizedStudentName}!`;
    lastRecognitionTime = Date.now();

    showToast({
      message: `Đã điểm danh cho ${recognizedStudentName}`,
      type: "success",
    });

    setTimeout(() => {
      if (Date.now() - lastRecognitionTime >= recognitionCooldown) {
        statusMessage = "Đang chờ nhận diện khuôn mặt...";
        recognizedStudentId = null;
        recognizedStudentName = null;
      }
    }, recognitionCooldown);
  }

  function handleRegistration(result: any) {
    statusMessage = `Đã đăng ký khuôn mặt thành công!`;
    showToast({
      message: `Đăng ký khuôn mặt thành công! ID: ${result.face_id}`,
      type: "success",
    });

    setTimeout(() => {
      statusMessage = "Chọn lớp và đăng ký khuôn mặt học sinh mới.";
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

<svelte:head>
  <title
    >{mode === "attendance" ? "Điểm danh" : "Đăng ký khuôn mặt"} - Attendde</title
  >
</svelte:head>

<div
  class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col"
>
  <!-- Header Bar -->
  <header
    class="bg-black/30 backdrop-blur-sm border-b border-white/10 px-4 py-3"
  >
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="bg-primary/20 p-2 rounded-lg">
          <ScanFace class="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 class="text-white font-bold text-lg">Attendde Kiosk</h1>
          <p class="text-white/60 text-xs">{formatDate(currentTime)}</p>
        </div>
      </div>

      <!-- Time Display -->
      <div class="text-right">
        <p class="text-3xl font-mono font-bold text-white tracking-wider">
          {formatTime(currentTime)}
        </p>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex-1 flex items-center justify-center p-4 md:p-8">
    <div class="w-full max-w-4xl">
      <!-- Mode Tabs -->
      <div class="flex justify-center mb-6">
        <div class="bg-white/10 backdrop-blur-sm p-1 rounded-xl inline-flex">
          <button
            class="px-6 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 {mode ===
            'attendance'
              ? 'bg-primary text-white shadow-lg'
              : 'text-white/70 hover:text-white hover:bg-white/10'}"
            onclick={() => switchMode("attendance")}
          >
            <ScanFace class="h-5 w-5" />
            Điểm danh
          </button>
          <button
            class="px-6 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 {mode ===
            'registration'
              ? 'bg-primary text-white shadow-lg'
              : 'text-white/70 hover:text-white hover:bg-white/10'}"
            onclick={() => switchMode("registration")}
          >
            <UserPlus class="h-5 w-5" />
            Đăng ký mới
          </button>
        </div>
      </div>

      <!-- Camera Container -->
      <div
        class="bg-black/40 backdrop-blur-sm rounded-2xl overflow-hidden shadow-2xl border border-white/10"
      >
        <!-- Camera View -->
        <div class="relative" style="aspect-ratio: 16/9;">
          <video
            bind:this={videoElement}
            autoplay
            muted
            playsinline
            disablepictureinpicture
            class="h-full w-full object-cover"
          ></video>

          <!-- Scanning Frame Overlay -->
          {#if isCameraReady && mode === "attendance" && !shouldShowRecognitionOverlay}
            <div
              class="absolute inset-0 flex items-center justify-center pointer-events-none"
            >
              <div class="relative w-64 h-64 md:w-80 md:h-80">
                <!-- Corner brackets -->
                <div
                  class="absolute top-0 left-0 w-12 h-12 border-t-4 border-l-4 border-primary rounded-tl-xl"
                ></div>
                <div
                  class="absolute top-0 right-0 w-12 h-12 border-t-4 border-r-4 border-primary rounded-tr-xl"
                ></div>
                <div
                  class="absolute bottom-0 left-0 w-12 h-12 border-b-4 border-l-4 border-primary rounded-bl-xl"
                ></div>
                <div
                  class="absolute bottom-0 right-0 w-12 h-12 border-b-4 border-r-4 border-primary rounded-br-xl"
                ></div>

                <!-- Scanning line animation -->
                {#if !isProcessing}
                  <div
                    class="absolute inset-x-4 top-4 h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent animate-pulse"
                  ></div>
                {/if}
              </div>
            </div>
          {/if}

          <!-- Loading State -->
          {#if !isCameraReady && cameraSupported}
            <div
              class="absolute inset-0 flex flex-col items-center justify-center bg-black/80"
            >
              <Loader2 class="h-12 w-12 text-primary animate-spin mb-4" />
              <p class="text-white/80 font-medium">Đang khởi tạo camera...</p>
            </div>
          {/if}

          <!-- Processing State -->
          {#if isProcessing && isCameraReady}
            <div
              class="absolute inset-0 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm"
            >
              <div class="bg-white/10 rounded-2xl p-8 text-center">
                <Loader2
                  class="h-16 w-16 text-primary animate-spin mx-auto mb-4"
                />
                <p class="text-white text-xl font-medium">Đang nhận diện...</p>
              </div>
            </div>
          {/if}

          <!-- Recognition Success Overlay -->
          {#if shouldShowRecognitionOverlay}
            <div
              class="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm"
            >
              <div
                class="bg-success/90 rounded-3xl p-8 md:p-12 text-center text-white shadow-2xl transform animate-pulse"
              >
                <div class="bg-white/20 rounded-full p-4 w-fit mx-auto mb-4">
                  <CheckCircle class="h-16 w-16 md:h-20 md:w-20" />
                </div>
                <h2 class="text-3xl md:text-4xl font-bold mb-2">Xin chào!</h2>
                <p class="text-2xl md:text-3xl font-medium opacity-90">
                  {recognizedStudentName || recognizedStudentId}
                </p>
                <p class="text-sm mt-4 opacity-75">
                  Điểm danh thành công lúc {formatTime(new Date())}
                </p>
              </div>
            </div>
          {/if}

          <!-- Camera Error State -->
          {#if !cameraSupported}
            <div
              class="absolute inset-0 flex flex-col items-center justify-center bg-black/90"
            >
              <div class="text-center p-8">
                <div class="bg-error/20 rounded-full p-4 w-fit mx-auto mb-4">
                  <CameraOff class="h-12 w-12 text-error" />
                </div>
                <h3 class="text-white text-xl font-bold mb-2">
                  Không thể truy cập camera
                </h3>
                <p class="text-white/60 mb-6 max-w-md">
                  {errorMessage ||
                    "Vui lòng kiểm tra quyền truy cập camera trong cài đặt trình duyệt."}
                </p>

                <div class="flex flex-col sm:flex-row gap-3 justify-center">
                  <button
                    class="btn btn-primary gap-2"
                    onclick={() => setupCamera()}
                  >
                    <RefreshCw class="h-4 w-4" />
                    Thử lại
                  </button>
                  <label class="btn btn-outline btn-primary gap-2">
                    <Camera class="h-4 w-4" />
                    Chụp từ thiết bị
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
            </div>
          {/if}
        </div>

        <!-- Status Bar -->
        <div
          class="bg-black/50 px-4 py-3 flex items-center justify-between border-t border-white/10"
        >
          <div class="flex items-center gap-3">
            <span
              class="h-3 w-3 rounded-full transition-colors"
              class:bg-success={isCameraReady && !isProcessing}
              class:bg-warning={isProcessing}
              class:bg-error={!isCameraReady && !cameraSupported}
              class:animate-pulse={isProcessing ||
                (!isCameraReady && cameraSupported)}
            ></span>
            <p class="text-white/80 text-sm font-medium">
              {#if errorMessage}
                <span class="text-error">{errorMessage}</span>
              {:else}
                {statusMessage}
              {/if}
            </p>
          </div>

          {#if mode === "attendance"}
            <div class="text-white/50 text-xs flex items-center gap-2">
              <ScanFace class="h-4 w-4" />
              Tự động quét mỗi 2 giây
            </div>
          {/if}
        </div>

        <!-- Registration Form -->
        {#if mode === "registration"}
          <div class="bg-white/5 p-6 border-t border-white/10">
            <div class="max-w-md mx-auto space-y-4">
              <div class="form-control">
                <label for="classId" class="label">
                  <span
                    class="label-text text-white/80 font-medium flex items-center gap-2"
                  >
                    <School class="h-4 w-4" />
                    Chọn lớp học
                  </span>
                </label>
                <select
                  bind:value={selectedClassId}
                  id="classId"
                  class="select select-bordered bg-white/10 border-white/20 text-white w-full"
                  required
                >
                  <option disabled selected value={null} class="text-black"
                    >-- Chọn lớp --</option
                  >
                  {#each data.classes as cls}
                    <option value={cls.id} class="text-black">{cls.name}</option
                    >
                  {/each}
                </select>
              </div>

              <button
                class="btn btn-primary w-full gap-2 h-12"
                onclick={() =>
                  captureAndProcess(
                    "/api/students/register-face",
                    handleRegistration,
                  )}
                disabled={selectedClassId === null || !canCapture}
              >
                {#if isProcessing}
                  <Loader2 class="h-5 w-5 animate-spin" />
                  Đang xử lý...
                {:else}
                  <UserPlus class="h-5 w-5" />
                  Đăng ký khuôn mặt
                {/if}
              </button>

              <p class="text-center text-white/40 text-xs">
                Hướng mặt vào camera và giữ yên khi nhấn nút đăng ký
              </p>
            </div>
          </div>
        {/if}
      </div>

      <!-- Instructions -->
      <div class="mt-6 text-center">
        <p class="text-white/50 text-sm">
          {#if mode === "attendance"}
            Nhìn thẳng vào camera để điểm danh tự động
          {:else}
            Chọn lớp, hướng mặt vào camera và nhấn "Đăng ký khuôn mặt"
          {/if}
        </p>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="bg-black/30 border-t border-white/10 px-4 py-3">
    <div
      class="max-w-6xl mx-auto flex items-center justify-between text-white/40 text-xs"
    >
      <p>© {new Date().getFullYear()} Attendde</p>
      <p class="flex items-center gap-2">
        {#if isCameraReady}
          <Camera class="h-3 w-3 text-success" />
          Camera đang hoạt động
        {:else}
          <CameraOff class="h-3 w-3 text-error" />
          Camera không khả dụng
        {/if}
      </p>
    </div>
  </footer>
</div>

<canvas bind:this={canvasElement} class="hidden" aria-hidden="true"></canvas>

<style>
  video {
    transform: scaleX(-1);
  }
</style>
