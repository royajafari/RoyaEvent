import react from "@vitejs/plugin-react-swc";
import { defineConfig } from "vitest/config";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    // pool پیش‌فرض ("forks") تو این محیط (ساندباکس ویندوز) روی spawn کردن
    // child process گیر می‌کنه و timeout می‌ده؛ "threads" (worker_threads،
    // نه process جدا) قابل‌اعتماده و سریع‌تره، برای این پروژه هیچ ریسکی هم
    // نداره چون تستامون نیازی به ایزوله‌سازی سطح پردازه ندارن.
    pool: "threads",
  },
});
