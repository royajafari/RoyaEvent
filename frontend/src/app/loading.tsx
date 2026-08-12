import { RoyaEventLoader } from "@/components/RoyaEventLoader";

// فایل ویژه‌ی Next.js: به‌صورت خودکار در هر انتقال مسیر/بارگذاری داده که
// طول بکشه، به‌جای محتوای صفحه نشون داده می‌شه (Suspense boundary) و با
// آماده‌شدن محتوا خودش کنار می‌ره — بدون نیاز به کنترل دستی state.
export default function Loading() {
  return <RoyaEventLoader />;
}
