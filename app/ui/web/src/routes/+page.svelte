<script lang="ts">
  import {
    ArrowRight,
    Award,
    Brain,
    Check,
    Activity,
    Eye,
    Heart,
    Shield,
    MessageCircle,
    Sparkles,
    TrendingUp,
    Users,
    Zap,
    School,
    GraduationCap,
    FileText,
    BarChart3,
  } from "lucide-svelte";
  import { onMount } from "svelte";

  // Placeholder image for educational/tech background
  const HeroBg =
    "https://images.unsplash.com/photo-1523240795612-9a054b0db644?q=80&w=2940&auto=format&fit=crop";

  let isVisible = $state(false);
  let statsVisible = $state(false);

  onMount(() => {
    isVisible = true;

    // Animate stats when scrolled into view
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            statsVisible = true;
          }
        });
      },
      { threshold: 0.3 },
    );

    const statsSection = document.querySelector("#stats-section");
    if (statsSection) observer.observe(statsSection);

    return () => observer.disconnect();
  });
</script>

<svelte:head>
  <title>Attendde - Hệ thống Điểm danh & Quản lý AI</title>
  <meta
    name="description"
    content="Giải pháp quản lý điểm danh toàn diện với công nghệ AI điểm danh và hỗ trợ giải quyết yêu cầu tự động."
  />
</svelte:head>

<div class="bg-base-100 min-h-screen overflow-x-hidden font-sans">
  <!-- Hero Section -->
  <div
    class="relative h-[70vh] min-h-[500px] w-full overflow-hidden md:h-[80vh] md:min-h-[600px]"
  >
    <!-- Parallax Background -->
    <div class="absolute inset-0">
      <img
        src={HeroBg}
        alt="Smart Education"
        class="h-full w-full scale-105 object-cover transition-transform duration-[8000ms] brightness-50"
        style="transform: translateY({isVisible ? '0' : '-5%'})"
      />
      <div
        class="absolute inset-0 bg-gradient-to-b from-slate-900/80 via-blue-900/60 to-slate-900/90"
      ></div>

      <!-- Animated overlay pattern -->
      <div class="absolute inset-0 opacity-20">
        <div
          class="absolute inset-0"
          style="background-image: radial-gradient(circle at 2px 2px, rgba(255,255,255,0.3) 1px, transparent 0); background-size: 40px 40px;"
        ></div>
      </div>
    </div>

    <!-- Content -->
    <div
      class="relative container mx-auto flex h-full flex-col items-center justify-center px-4 text-center"
    >
      <div
        class="max-w-5xl space-y-4 md:space-y-6"
        style="opacity: {isVisible
          ? '1'
          : '0'}; transform: translateY({isVisible
          ? '0'
          : '20px'}); transition: all 1s ease-out"
      >
        <!-- Badge -->
        <div
          class="bg-blue-500/20 border-blue-400/30 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold text-white backdrop-blur-sm md:px-6 md:py-2.5 md:text-sm"
        >
          <Brain size={16} class="animate-pulse text-blue-300" />
          <span>Trí tuệ nhân tạo thế hệ mới cho giáo dục</span>
        </div>

        <h1
          class="font-montserrat text-3xl leading-tight font-black tracking-tight text-white sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl"
        >
          Điểm danh thông minh &<br />
          Kết nối nhà trường
        </h1>

        <p
          class="mx-auto max-w-2xl text-base leading-relaxed font-light text-blue-50 md:text-lg lg:text-xl"
        >
          Hệ thống tự động hóa điểm danh bằng AI, hỗ trợ giáo viên giải quyết
          yêu cầu của phụ huynh tức thì, và mang lại sự an tâm tuyệt đối cho nhà
          trường.
        </p>

        <!-- CTA Buttons -->
        <div
          class="flex flex-col justify-center gap-3 pt-4 sm:flex-row md:gap-4 md:pt-6"
        >
          <a
            href="/login"
            class="btn btn-primary btn-lg shadow-primary/25 hover:shadow-primary/40 gap-2 text-base shadow-xl transition-all hover:-translate-y-0.5 hover:shadow-2xl md:text-lg"
          >
            Đăng nhập hệ thống
            <ArrowRight size={20} />
          </a>
          <a
            href="#features"
            class="btn btn-ghost btn-lg hover:bg-white/10 border-white/50 text-base text-white transition-all md:text-lg"
          >
            Tìm hiểu tính năng
          </a>
        </div>
      </div>
    </div>
  </div>

  <!-- Stats Section -->
  <section
    id="stats-section"
    class="from-blue-50 via-white to-blue-50 border-base-200 border-y bg-gradient-to-br py-12 md:py-16"
  >
    <div class="container mx-auto max-w-6xl px-4">
      <div class="grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-8">
        {#each [{ value: "99.9%", label: "Độ chính xác AI", icon: Check }, { value: "500+", label: "Trường học tin dùng", icon: School }, { value: "1M+", label: "Lượt điểm danh/ngày", icon: Users }, { value: "2s", label: "Thời gian xử lý", icon: Zap }] as stat, i}
          <div
            class="bg-white/80 border-blue-100 hover:border-primary/30 group rounded-2xl border p-4 text-center backdrop-blur-sm transition-all hover:shadow-lg md:p-6"
            style="opacity: {statsVisible
              ? '1'
              : '0'}; transform: translateY({statsVisible
              ? '0'
              : '20px'}); transition: all 0.6s ease-out {i * 0.1}s"
          >
            <svelte:component
              this={stat.icon}
              size={28}
              class="text-primary mx-auto mb-2 transition-transform group-hover:scale-110 md:mb-3"
            />
            <div
              class="text-base-content mb-1 text-2xl font-black md:mb-2 md:text-3xl lg:text-4xl"
            >
              {stat.value}
            </div>
            <div class="text-base-content/60 text-xs font-medium md:text-sm">
              {stat.label}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Problem/Solution Section -->
  <section id="features" class="py-16 md:py-24 lg:py-32">
    <div class="container mx-auto max-w-6xl px-4">
      <div
        class="grid grid-cols-1 items-center gap-8 md:gap-12 lg:grid-cols-2 lg:gap-16"
      >
        <!-- Text Content -->
        <div class="space-y-4 md:space-y-6">
          <div
            class="text-primary inline-flex items-center gap-2 text-sm font-bold tracking-wider uppercase md:text-base"
          >
            <div class="bg-primary h-0.5 w-8 md:w-12"></div>
            <span>Vấn đề & Giải pháp</span>
          </div>

          <h2
            class="font-montserrat text-3xl leading-tight font-bold text-gray-900 sm:text-4xl md:text-5xl"
          >
            Xóa bỏ nỗi lo <br />
            <span class="text-primary relative inline-block">
              "Quản lý thủ công"
              <svg
                class="absolute -bottom-2 left-0 w-full"
                height="8"
                viewBox="0 0 200 8"
                fill="none"
              >
                <path
                  d="M1 5.5C50 1.5 150 1.5 199 5.5"
                  stroke="currentColor"
                  stroke-width="3"
                  stroke-linecap="round"
                />
              </svg>
            </span>
          </h2>

          <div
            class="space-y-4 text-base leading-relaxed text-gray-600 md:text-lg"
          >
            <p class="flex items-start gap-3">
              <Activity size={24} class="text-error mt-1 shrink-0" />
              <span>
                Điểm danh giấy tốn thời gian, dễ sai sót và khó tổng hợp báo
                cáo.
              </span>
            </p>
            <p class="flex items-start gap-3">
              <MessageCircle size={24} class="text-error mt-1 shrink-0" />
              <span>
                Giáo viên quá tải với quá nhiều tin nhắn xin phép, hỏi thăm từ
                phụ huynh mỗi ngày.
              </span>
            </p>
            <div
              class="bg-primary/5 border-primary rounded-r-xl border-l-4 p-4 md:p-6"
            >
              <p class="text-base-content font-semibold">
                <strong class="text-primary"
                  >Attendde giải quyết triệt để.</strong
                >
                Camera AI tự động nhận diện học sinh khi vào lớp. Trợ lý ảo AI giúp
                giáo viên phân loại và soạn thảo phản hồi cho phụ huynh ngay lập tức.
              </p>
            </div>
          </div>
        </div>

        <!-- Visual Cards (Features) -->
        <div class="grid grid-cols-2 gap-3 md:gap-4">
          <div class="space-y-3 md:space-y-4">
            <div
              class="from-blue-50 to-blue-100 border-blue-200 hover:border-primary/40 group rounded-2xl border bg-gradient-to-br p-4 transition-all hover:shadow-xl md:rounded-3xl md:p-6 lg:p-8"
            >
              <div
                class="bg-blue-500/10 mb-3 flex h-12 w-12 items-center justify-center rounded-2xl transition-transform group-hover:scale-110 md:mb-4 md:h-14 md:w-14 lg:h-16 lg:w-16"
              >
                <Eye size={28} class="text-primary md:h-8 md:w-8" />
              </div>
              <h3 class="mb-2 text-base font-bold md:text-lg lg:text-xl">
                Smart Tracking
              </h3>
              <p class="text-xs leading-relaxed text-gray-600 md:text-sm">
                Camera nhận diện khuôn mặt chính xác
              </p>
            </div>

            <div
              class="from-purple-50 to-purple-100 border-purple-200 hover:border-purple-400 group rounded-2xl border bg-gradient-to-br p-4 transition-all hover:shadow-xl md:rounded-3xl md:p-6 lg:p-8"
            >
              <div
                class="bg-purple-500/10 mb-3 flex h-12 w-12 items-center justify-center rounded-2xl transition-transform group-hover:scale-110 md:mb-4 md:h-14 md:w-14 lg:h-16 lg:w-16"
              >
                <Brain size={28} class="text-purple-600 md:h-8 md:w-8" />
              </div>
              <h3 class="mb-2 text-base font-bold md:text-lg lg:text-xl">
                AI Assistant
              </h3>
              <p class="text-xs leading-relaxed text-gray-600 md:text-sm">
                Hỗ trợ tự động trả lời đơn xin phép của phụ huynh
              </p>
            </div>
          </div>

          <div class="mt-8 space-y-3 md:mt-12 md:space-y-4">
            <div
              class="from-green-50 to-green-100 border-green-200 hover:border-green-400 group rounded-2xl border bg-gradient-to-br p-4 transition-all hover:shadow-xl md:rounded-3xl md:p-6 lg:p-8"
            >
              <div
                class="bg-green-500/10 mb-3 flex h-12 w-12 items-center justify-center rounded-2xl transition-transform group-hover:scale-110 md:mb-4 md:h-14 md:w-14 lg:h-16 lg:w-16"
              >
                <BarChart3 size={28} class="text-green-600 md:h-8 md:w-8" />
              </div>
              <h3 class="mb-2 text-base font-bold md:text-lg lg:text-xl">
                Analytics
              </h3>
              <p class="text-xs leading-relaxed text-gray-600 md:text-sm">
                Báo cáo chuyên cần theo thời gian thực
              </p>
            </div>

            <div
              class="group rounded-2xl border border-orange-200 bg-gradient-to-br from-orange-50 to-orange-100 p-4 transition-all hover:border-orange-400 hover:shadow-xl md:rounded-3xl md:p-6 lg:p-8"
            >
              <div
                class="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-500/10 transition-transform group-hover:scale-110 md:mb-4 md:h-14 md:w-14 lg:h-16 lg:w-16"
              >
                <Shield size={28} class="text-orange-600 md:h-8 md:w-8" />
              </div>
              <h3 class="mb-2 text-base font-bold md:text-lg lg:text-xl">
                Bảo mật
              </h3>
              <p class="text-xs leading-relaxed text-gray-600 md:text-sm">
                Dữ liệu được mã hóa an toàn tuyệt đối
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Roles & Technology Section -->
  <section
    class="from-slate-50 to-slate-100 bg-gradient-to-b py-16 md:py-24 lg:py-32"
  >
    <div class="container mx-auto max-w-6xl px-4">
      <div class="mb-12 text-center md:mb-16">
        <div
          class="text-primary mb-4 inline-flex items-center gap-2 text-sm font-bold tracking-wider uppercase md:text-base"
        >
          <Users size={20} />
          <span>Hệ sinh thái</span>
        </div>
        <h2
          class="font-montserrat mb-4 text-3xl font-bold text-gray-900 sm:text-4xl md:mb-6 md:text-5xl"
        >
          Tính năng cho từng vai trò
        </h2>
        <p class="mx-auto max-w-2xl text-base text-gray-600 md:text-lg">
          Kết nối chặt chẽ giữa Gia đình và Nhà trường trên một nền tảng duy
          nhất
        </p>
      </div>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-6 lg:gap-8">
        {#each [{ icon: School, color: "blue", role: "Quản trị viên (Admin)", desc: "Quản lý toàn diện hệ thống nhân sự và học sinh.", features: ["Thêm/Sửa tài khoản GV & HS", "Phân tích dữ liệu toàn trường", "Cấu hình hệ thống AI"] }, { icon: GraduationCap, color: "purple", role: "Giáo viên (Teacher)", desc: "Giảm tải công việc hành chính, tập trung vào chuyên môn.", features: ["Quản lý hồ sơ học sinh", "AI hỗ trợ xử lý đơn xin của phụ huynh", "Xem báo cáo lớp chủ nhiệm"] }, { icon: Heart, color: "green", role: "Phụ huynh (Parent)", desc: "Luôn nắm bắt tình hình của con mọi lúc mọi nơi.", features: ["Xem điểm danh Real-time", "Tạo đơn gửi giáo viên", "Nhận thông báo tự động"] }] as item, i}
          <div
            class="group bg-white border-base-200 rounded-2xl border p-6 shadow-md transition-all hover:shadow-2xl md:rounded-3xl md:p-8 hover:border-{item.color}-200 hover:-translate-y-2"
            style="transition-delay: {i * 0.1}s"
          >
            <div
              class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-{item.color}-50 transition-transform group-hover:scale-110 group-hover:rotate-3 md:mb-6 md:h-16 md:w-16"
            >
              <svelte:component
                this={item.icon}
                size={28}
                class="text-{item.color}-600 md:h-8 md:w-8"
              />
            </div>

            <h3 class="mb-3 text-lg font-bold md:text-xl text-gray-800">
              {item.role}
            </h3>
            <p
              class="mb-4 text-sm leading-relaxed text-gray-600 md:mb-6 md:text-base"
            >
              {item.desc}
            </p>

            <ul class="space-y-3">
              {#each item.features as feature}
                <li
                  class="flex items-center gap-3 text-xs text-gray-600 md:text-sm"
                >
                  <div
                    class="h-6 w-6 rounded-full bg-{item.color}-100 flex items-center justify-center shrink-0"
                  >
                    <Check size={14} class="text-{item.color}-600" />
                  </div>
                  {feature}
                </li>
              {/each}
            </ul>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Core Values Section -->
  <section class="bg-white py-16 md:py-24 lg:py-32">
    <div class="container mx-auto max-w-6xl px-4">
      <div class="mb-12 text-center md:mb-16">
        <div
          class="text-primary mb-4 inline-flex items-center gap-2 text-sm font-bold tracking-wider uppercase md:text-base"
        >
          <Shield size={20} />
          <span>Giá trị cốt lõi</span>
        </div>
        <h2
          class="font-montserrat text-3xl font-bold text-gray-900 sm:text-4xl md:text-5xl"
        >
          Tại sao chọn Attendde?
        </h2>
      </div>

      <div class="grid grid-cols-1 gap-6 md:grid-cols-3 md:gap-8 lg:gap-12">
        {#each [{ icon: Brain, title: "AI xử lý đơn xin phép", desc: "Không chỉ là điểm danh. AI của chúng tôi phân tích nội dung đơn xin phép từ phụ huynh (xin nghỉ, thuốc men, dặn dò) và gợi ý câu trả lời phù hợp nhất cho giáo viên.", gradient: "from-blue-950/5 to-blue-950/15" }, { icon: Eye, title: "Minh bạch & Tức thì", desc: "Phụ huynh nhận được thông báo ngay khi con bước vào lớp. Mọi dữ liệu điểm danh đều được ghi lại minh bạch, không thể sửa đổi thủ công trái phép.", gradient: "from-green-950/5 to-green-950/15" }, { icon: TrendingUp, title: "Phân tích Dữ liệu", desc: "Dashboard dành cho Admin cung cấp cái nhìn tổng quan về tỉ lệ chuyên cần, xu hướng nghỉ học, giúp nhà trường đưa ra quyết định kịp thời.", gradient: "from-purple-950/5 to-purple-950/15" }] as value, i}
          <div
            class="group text-center transition-all hover:-translate-y-2"
            style="transition-delay: {i * 0.1}s"
          >
            <div
              class="bg-gradient-to-br {value.gradient} border-base-200 hover:border-primary/30 h-full rounded-2xl border p-6 transition-all hover:shadow-xl md:rounded-3xl md:p-8"
            >
              <div
                class="bg-white mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl shadow-sm transition-transform group-hover:scale-110 group-hover:rotate-6 md:mb-6 md:h-20 md:w-20"
              >
                <svelte:component
                  this={value.icon}
                  size={32}
                  class="text-gray-700 md:h-10 md:w-10"
                  strokeWidth={1.5}
                />
              </div>

              <h3
                class="mb-3 text-lg font-bold md:mb-4 md:text-xl lg:text-2xl text-gray-800"
              >
                {value.title}
              </h3>
              <p
                class="text-justify text-sm leading-relaxed text-gray-600 md:text-base"
              >
                {value.desc}
              </p>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- CTA Section -->
  <section class="relative overflow-hidden py-20 md:py-28 lg:py-32">
    <!-- Gradient Background -->
    <div
      class="from-blue-950/95 via-blue-950 to-indigo-900 absolute inset-0 bg-linear-to-br"
    ></div>

    <!-- Animated Pattern -->
    <div class="absolute inset-0 opacity-10">
      <div
        class="absolute inset-0"
        style="background-image: radial-gradient(circle at 2px 2px, white 1px, transparent 0); background-size: 60px 60px;"
      ></div>
    </div>

    <!-- Floating shapes -->
    <div
      class="absolute top-10 left-10 h-32 w-32 animate-pulse rounded-full bg-white/10 blur-3xl"
    ></div>
    <div
      class="absolute right-10 bottom-10 h-40 w-40 animate-pulse rounded-full bg-white/10 blur-3xl"
      style="animation-delay: 1s"
    ></div>

    <!-- Content -->
    <div class="relative container mx-auto px-4">
      <div
        class="mx-auto max-w-6xl space-y-6 text-center text-white md:space-y-8"
      >
        <div
          class="inline-flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-xs font-semibold backdrop-blur-sm md:px-6 md:py-2.5 md:text-sm"
        >
          <Sparkles size={16} />
          <span>Chuyển đổi số cho trường học ngay hôm nay</span>
        </div>

        <h2
          class="font-montserrat text-3xl leading-tight font-bold sm:text-4xl md:text-5xl lg:text-6xl"
        >
          Xây dựng trường học thông minh<br class="hidden sm:block" />
          với Attendde
        </h2>

        <p
          class="mx-auto text-base leading-relaxed text-white/90 md:text-lg lg:text-xl"
        >
          Trải nghiệm sự khác biệt của công nghệ AI trong quản lý giáo dục.
        </p>

        <div
          class="flex flex-col justify-center gap-3 pt-4 sm:flex-row md:gap-4 md:pt-6"
        >
          <a
            href="/login"
            class="btn btn-lg text-primary gap-2 border-none bg-white text-base shadow-xl transition-all hover:-translate-y-1 hover:bg-gray-100 hover:shadow-2xl md:text-lg"
          >
            <Users size={20} />
            Đăng nhập
          </a>
          <a
            href="/contact"
            class="btn btn-lg btn-outline hover:text-primary gap-2 border-2 border-white text-base text-white transition-all hover:bg-white md:text-lg"
          >
            <FileText size={20} />
            Liên hệ Demo
          </a>
        </div>

        <!-- Trust indicators -->
        <div
          class="flex flex-wrap items-center justify-center gap-4 pt-8 text-xs text-white/80 md:gap-8 md:pt-12 md:text-sm"
        >
          <div class="flex items-center gap-2">
            <Check size={16} class="text-white" />
            <span>Bảo mật dữ liệu</span>
          </div>
          <div class="flex items-center gap-2">
            <Check size={16} class="text-white" />
            <span>Hỗ trợ kỹ thuật 24/7</span>
          </div>
          <div class="flex items-center gap-2">
            <Check size={16} class="text-white" />
            <span>Triển khai dễ dàng</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>

<style>
  /* Smooth animations */
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Hide scrollbar for horizontal scroll */
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
</style>
