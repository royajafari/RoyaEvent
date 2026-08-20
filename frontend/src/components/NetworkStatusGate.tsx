"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { WifiOff } from "lucide-react";

import { useNetworkStatus } from "@/hooks/useNetworkStatus";
import { refreshAccessToken } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";

// بخش ۱۲ architecture.md (نیازمندی ۳۳): دو رفتار جدا برای قطع اتصال —
//  ۱) کاربر لاگین‌کرده: هیچ UI بلاک‌کننده‌ای نشون نده (بذار با کش/داده‌ی
//     موجود کار کنه)، فقط بعد از اتصال مجدد واقعی یک رفرش خاموش توکن انجام
//     بده؛ اگه رفرش شکست خورد (یعنی کوکی رفرش‌توکن هم در این فاصله منقضی/
//     باطل شده) به صفحه‌ی ورود بفرست.
//  ۲) کاربر لاگین‌نکرده: یک اسکلت تمام‌صفحه نشون بده تا اتصال واقعی
//     (نه فقط رویداد online مرورگر) برقرار بشه — چون بدون لاگین چیزی برای
//     محافظت‌کردن با رفرش خاموش نیست، و محتوای بدون لاگین اغلب به هر حال
//     SSR/fetch تازه نیاز داره.
export function NetworkStatusGate({ children }: { children: React.ReactNode }) {
  const isOnline = useNetworkStatus();
  const accessToken = useAuthStore((s) => s.accessToken);
  const router = useRouter();
  const wasOffline = useRef(false);

  useEffect(() => {
    if (!isOnline) {
      wasOffline.current = true;
      return;
    }
    if (!wasOffline.current) return;
    wasOffline.current = false;

    if (accessToken) {
      refreshAccessToken().then((token) => {
        if (!token) router.push("/login");
      });
    }
  }, [isOnline, accessToken, router]);

  if (!isOnline && !accessToken) {
    return (
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-background">
        <WifiOff className="text-muted-foreground h-10 w-10 animate-pulse" />
        <p className="text-muted-foreground text-sm">در حال اتصال مجدد به اینترنت...</p>
      </div>
    );
  }

  return <>{children}</>;
}

export default NetworkStatusGate;
