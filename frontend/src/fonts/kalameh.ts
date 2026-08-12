import localFont from "next/font/local";

// فونت کلمه (Kalameh) — فونت اصلی RTL/فارسی پروژه.
// نکته‌ی لایسنس: کلمه یک فونت مالکیتی/تجاری (fontiran.com) است. فایل
// FontLicense.txt کنار فونت‌های اصلی (پوشه‌ی /font در ریشه‌ی ریپو) کد
// لایسنس ۶رقمی خالی دارد — قبل از انتشار عمومی/production، مطمئن شوید
// لایسنس وب معتبر برای این دامنه خریداری و کد آن درج شده است.
export const kalameh = localFont({
  variable: "--font-kalameh",
  display: "swap",
  src: [
    { path: "./kalameh/KalamehWeb-Thin.woff2", weight: "100", style: "normal" },
    { path: "./kalameh/KalamehWeb-ExtraLight.woff2", weight: "200", style: "normal" },
    { path: "./kalameh/KalamehWeb-Light.woff2", weight: "300", style: "normal" },
    { path: "./kalameh/KalamehWeb-Regular.woff2", weight: "400", style: "normal" },
    { path: "./kalameh/KalamehWeb-Medium.woff2", weight: "500", style: "normal" },
    { path: "./kalameh/KalamehWeb-SemiBold.woff2", weight: "600", style: "normal" },
    { path: "./kalameh/KalamehWeb-Bold.woff2", weight: "700", style: "normal" },
    { path: "./kalameh/KalamehWeb-ExtraBold.woff2", weight: "800", style: "normal" },
    { path: "./kalameh/KalamehWeb-Black.woff2", weight: "900", style: "normal" },
  ],
});
