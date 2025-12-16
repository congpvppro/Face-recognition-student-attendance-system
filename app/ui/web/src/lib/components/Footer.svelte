<script lang="ts">
  import {
    Shield,
    Facebook,
    Youtube,
    Linkedin,
    Mail,
    Phone,
    MapPin,
  } from "lucide-svelte";
</script>

<footer
  class="bg-base-200 text-base-content font-sans border-t border-base-300"
>
  <!-- Main content -->
  <div
    class="footer mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-10 md:flex-row md:flex-wrap md:px-6 lg:px-10"
  >
    <!-- Branding Column -->
    <aside class="flex-1 space-y-4">
      <div class="flex items-center gap-3">
        <div class="text-primary">
          <!-- SVG Shield Logo -->
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="h-10 w-10 md:h-12 md:w-12"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
            <path d="M12 8v4" />
            <path d="M12 16h.01" />
          </svg>
        </div>
        <div>
          <span
            class="font-montserrat block text-xl font-bold tracking-tight md:text-2xl"
            >Attendde</span
          >
          <span class="text-xs font-medium opacity-60 uppercase tracking-wider"
            >Education Platform 4.0</span
          >
        </div>
      </div>
      <p class="max-w-xs text-sm opacity-80 text-justify leading-relaxed">
        Giải pháp quản lý điểm danh toàn diện ứng dụng trí tuệ nhân tạo. Kết nối
        Nhà trường - Giáo viên - Phụ huynh trên một nền tảng duy nhất.
      </p>

      <!-- Social Links -->
      <div class="flex gap-4 mt-2">
        <a
          href="#"
          class="opacity-60 hover:opacity-100 hover:text-primary transition-all"
          ><Facebook size={20} /></a
        >
        <a
          href="#"
          class="opacity-60 hover:opacity-100 hover:text-error transition-all"
          ><Youtube size={20} /></a
        >
        <a
          href="#"
          class="opacity-60 hover:opacity-100 hover:text-blue-600 transition-all"
          ><Linkedin size={20} /></a
        >
      </div>
    </aside>

    <!-- Navigation Columns -->
    <nav class="min-w-[140px] flex-1 text-sm">
      <h6
        class="footer-title text-base-content/100 mb-3 text-xs font-bold uppercase tracking-widest opacity-50"
      >
        Sản phẩm
      </h6>
      <a
        href="/features"
        class="link-hover link mb-2 block opacity-80 hover:text-primary hover:opacity-100"
        >Tính năng nổi bật</a
      >
      <a
        href="/attendance"
        class="link-hover link mb-2 block opacity-80 hover:text-primary hover:opacity-100"
        >Kiosk điểm danh AI</a
      >
      <a
        href="/pricing"
        class="link-hover link mb-2 block opacity-80 hover:text-primary hover:opacity-100"
        >Bảng giá gói cước</a
      >
      <a
        href="/security"
        class="link-hover link mb-2 block opacity-80 hover:text-primary hover:opacity-100"
        >Bảo mật dữ liệu</a
      >
    </nav>

    <nav class="min-w-[140px] flex-1 text-sm">
      <h6
        class="footer-title text-base-content/100 mb-3 text-xs font-bold uppercase tracking-widest opacity-50"
      >
        Hỗ trợ
      </h6>
      <a
        href="/guides"
        class="link-hover link mb-2 block opacity-80 hover:text-primary hover:opacity-100"
        >Hướng dẫn sử dụng</a
      >
      <a
        href="/faq"
        class="link-hover link mb-2 block opacity-80 hover:text-primary hover:opacity-100"
        >Câu hỏi thường gặp</a
      >
      <a
        href="/privacy"
        class="link-hover link mb-2 block opacity-80 hover:text-primary hover:opacity-100"
        >Chính sách quyền riêng tư</a
      >
      <a
        href="/terms"
        class="link-hover link mb-2 block opacity-80 hover:text-primary hover:opacity-100"
        >Điều khoản dịch vụ</a
      >
    </nav>

    <!-- Contact Column -->
    <nav class="min-w-[200px] flex-1 text-sm">
      <h6
        class="footer-title text-base-content/100 mb-3 text-xs font-bold uppercase tracking-widest opacity-50"
      >
        Liên hệ
      </h6>
      <div class="flex flex-col gap-3 opacity-80">
        <div class="flex items-start gap-3">
          <MapPin size={18} class="shrink-0 mt-0.5" />
          <p>
            Tòa nhà EduTech, Khu Công nghệ cao Hòa Lạc,<br />
            Hà Nội, Việt Nam
          </p>
        </div>
        <div class="flex items-center gap-3">
          <Mail size={18} class="shrink-0" />
          <a
            href="mailto:support@attendde.edu.vn"
            class="link-hover link hover:text-primary"
          >
            support@attendde.edu.vn
          </a>
        </div>
        <div class="flex items-center gap-3">
          <Phone size={18} class="shrink-0" />
          <a
            href="tel:1900JQKA"
            class="link-hover link font-bold hover:text-primary">1900 JQKA</a
          >
        </div>
      </div>
    </nav>
  </div>

  <!-- Bottom bar -->
  <div class="border-base-300 border-t bg-base-300/30">
    <div
      class="footer footer-center text-base-content mx-auto w-full max-w-7xl px-4 py-4 md:px-6 lg:px-10"
    >
      <aside
        class="w-full flex flex-col md:flex-row justify-between items-center gap-2"
      >
        <p class="text-xs opacity-60">
          © {new Date().getFullYear()} Attendde Corporation. All rights reserved.
        </p>
        <div class="flex gap-4 text-xs opacity-60">
          <a href="/privacy" class="hover:underline">Privacy</a>
          <span>•</span>
          <a href="/terms" class="hover:underline">Terms</a>
          <span>•</span>
          <a href="/sitemap" class="hover:underline">Sitemap</a>
        </div>
      </aside>
    </div>
  </div>
</footer>
