"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, WifiOff } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";

// ErrorBoundary سراسری این اپ (app/error.tsx نکست‌جس — به‌صورت خودکار همه‌ی
// segmentهای زیر ریشه رو در بر می‌گیره، بدون نیاز به یک کلاس ErrorBoundary
// دستی). خطاهای شبکه‌ای رو از خطاهای واقعی رندر جدا می‌کنیم چون پیام و
// اقدام درست‌شون فرق داره: شبکه → «اتصالت رو چک کن»، رندر → پیام کلی‌تر.
//
// نکته: request() در lib/api-client.ts وقتی خود fetch throw کنه (نه پاسخ
// غیر-۲xx، بلکه کلاً network down) این خطا رو به ApiError تبدیل نمی‌کنه —
// یک TypeError خام مرورگری می‌مونه («Failed to fetch» کروم، «Load failed»
// سافاری) — پس باید هر دو مسیر (ApiError با status=۰ از آپلود XHR، و
// TypeError خام fetch) رو چک کنیم.
export function isLikelyNetworkError(error: Error): boolean {
  if (error instanceof ApiError) return error.status === 0;
  return /failed to fetch|networkerror|load failed/i.test(error.message);
}

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const network = isLikelyNetworkError(error);

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 py-24 text-center">
      {network ? (
        <WifiOff className="text-muted-foreground h-10 w-10" />
      ) : (
        <AlertTriangle className="text-destructive h-10 w-10" />
      )}
      <h2 className="text-lg font-bold">
        {network ? "ارتباط با سرور برقرار نشد" : "خطای غیرمنتظره‌ای رخ داد"}
      </h2>
      <p className="text-muted-foreground max-w-md text-sm">
        {network
          ? "اتصال اینترنت خود را بررسی کنید و دوباره تلاش کنید."
          : "این مشکل ثبت شد؛ می‌توانید دوباره تلاش کنید یا به صفحه‌ی اصلی برگردید."}
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => reset()}
          className={buttonVariants({ className: "gap-2" })}
        >
          <RefreshCw className="h-4 w-4" />
          تلاش دوباره
        </button>
        <Link href="/" className={buttonVariants({ variant: "outline" })}>
          بازگشت به خانه
        </Link>
      </div>
    </div>
  );
}
