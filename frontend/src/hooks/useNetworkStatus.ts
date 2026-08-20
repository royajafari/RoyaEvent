"use client";

import { useEffect, useState } from "react";

import { API_BASE_URL } from "@/lib/api-client";

// API_BASE_URL شامل /api/v1 است، ولی /health بک‌اند (app/main.py) عمداً
// بیرون از api_v1_prefix تعریف شده (مثل هر health-check معمول) — پس باید
// prefix رو حذف کنیم، نه مستقیم بهش append کنیم.
const HEALTH_URL = `${new URL(API_BASE_URL).origin}/health`;

const POLL_INTERVAL_MS = 15000;

// بخش ۱۲ architecture.md (نیازمندی ۳۳، «مقاومت در برابر قطع اتصال»):
// رویداد online/offline مرورگر به‌تنهایی کافی نیست — یعنی فقط «به یک شبکه
// وصلی» نه «واقعاً به اینترنت/سرور ما وصلی» (مثلاً وای‌فای بدون اینترنت
// واقعی). پس یک پینگ دوره‌ای سبک به /health هم لازمه تا وضعیت واقعی رو
// تأیید کنه.
//
// نکته‌ی مهم پیاده‌سازی: checkHealth عمداً async نیست (به‌جاش زنجیره‌ی
// .then/.catch داره) — دقیقاً همون الگوی loadTickets در app/tickets/page.tsx.
// یک تابع async محلی که بعد از await مستقیم setState صدا بزنه و از دل یک
// effect فراخوانی بشه، توسط قانون react-hooks/set-state-in-effect فلگ
// می‌شه؛ زنجیره‌ی .then() این مشکل رو نداره (نکته‌ی #۱۹ CLAUDE.md).
export function useNetworkStatus(): boolean {
  // همیشه true تو اولین رندر (چه سرور چه کلاینت) — خوندن navigator.onLine
  // مستقیم تو خود useState اینیشیالایزر یه hydration mismatch واقعی ایجاد
  // می‌کرد: سرور همیشه true رندر می‌کنه (navigator اونجا وجود نداره)، ولی
  // کلاینت موقع اولین رندر (پیش از هر effect) ممکنه navigator.onLine رو
  // false ببینه و بلافاصله با HTML سرور فرق کنه. مقدار واقعی رو effect زیر
  // (که فقط بعد از hydrate اجرا می‌شه) با checkHealth() تصحیح می‌کنه —
  // که هم دقیق‌تره (واقعاً سرور رو چک می‌کنه) هم امن برای SSR.
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    let cancelled = false;

    function checkHealth() {
      fetch(HEALTH_URL, { cache: "no-store" })
        .then((res) => {
          if (!cancelled) setIsOnline(res.ok);
        })
        .catch(() => {
          if (!cancelled) setIsOnline(false);
        });
    }

    function handleBrowserOffline() {
      setIsOnline(false);
    }

    window.addEventListener("online", checkHealth);
    window.addEventListener("offline", handleBrowserOffline);
    const timer = setInterval(checkHealth, POLL_INTERVAL_MS);
    checkHealth();

    return () => {
      cancelled = true;
      window.removeEventListener("online", checkHealth);
      window.removeEventListener("offline", handleBrowserOffline);
      clearInterval(timer);
    };
  }, []);

  return isOnline;
}

export default useNetworkStatus;
