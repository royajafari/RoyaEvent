import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // برای Dockerfile production — ایمیج سبک‌تر، بدون node_modules کامل
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
