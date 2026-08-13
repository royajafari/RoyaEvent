"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CircleHelp } from "lucide-react";

import { RoyaEventLogo } from "@/components/RoyaEventLogo";
import { Button, buttonVariants } from "@/components/ui/button";
import { authApi } from "@/lib/api-client";
import { startOnboardingTour } from "@/lib/onboarding-tour";
import { useAuthStore } from "@/store/auth-store";

export function SiteHeader() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const clearAuth = useAuthStore((s) => s.clear);

  useEffect(() => {
    if (!accessToken) return;
    authApi.me(accessToken).then(setUser).catch(() => {});
  }, [accessToken, setUser]);

  async function handleLogout() {
    clearAuth();
    try {
      await authApi.logout();
    } catch {
      // کوکی رفرش سمت سرور هم پاک می‌شه؛ اگه خود درخواست fail بشه، حالت
      // لاگین‌نکرده‌ی سمت کلاینت که همین الان clear شد کافیه
    }
    router.push("/");
    router.refresh();
  }

  return (
    <header className="border-border bg-background/95 sticky top-0 z-40 border-b backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
        <Link href="/" id="tour-logo" className="flex shrink-0 flex-col items-start gap-0.5">
          <RoyaEventLogo size={34} />
          <span className="text-muted-foreground text-xs sm:text-sm">
            رویا ایونت: تجربه رویداد و وبینار متفاوت
          </span>
        </Link>
        <nav className="flex flex-wrap items-center gap-1 sm:gap-2">
          <Link
            href="/events"
            id="tour-events"
            className={buttonVariants({ variant: "ghost", size: "sm", className: "text-base" })}
          >
            رویدادها
          </Link>
          <Link
            href="/events/mine"
            id="tour-mine"
            className={buttonVariants({ variant: "ghost", size: "sm", className: "text-base" })}
          >
            رویدادهای من
          </Link>
          <Link
            href="/tickets"
            id="tour-tickets"
            className={buttonVariants({ variant: "ghost", size: "sm", className: "text-base" })}
          >
            بلیط‌های من
          </Link>
          <Link
            href="/favorites"
            className={buttonVariants({ variant: "ghost", size: "sm", className: "text-base" })}
          >
            علاقه‌مندی‌ها
          </Link>
          <Link
            href="/follows"
            className={buttonVariants({ variant: "ghost", size: "sm", className: "text-base" })}
          >
            دنبال‌کردن‌ها
          </Link>
          <Link
            href="/events/create"
            id="tour-create"
            className={buttonVariants({ variant: "ghost", size: "sm", className: "text-base" })}
          >
            ایجاد رویداد
          </Link>
          {accessToken ? (
            <>
              <Link
                href="/profile"
                className={buttonVariants({
                  variant: "ghost",
                  size: "sm",
                  className: "gap-2 text-base",
                })}
              >
                {user?.avatar_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={user.avatar_url}
                    alt="عکس پروفایل"
                    className="h-6 w-6 rounded-full object-cover"
                  />
                ) : null}
                پروفایل
              </Link>
              <Button
                id="tour-login"
                variant="outline"
                size="sm"
                className="text-base"
                onClick={handleLogout}
              >
                خروج
              </Button>
            </>
          ) : (
            <Link
              href="/login"
              id="tour-login"
              className={buttonVariants({ variant: "outline", size: "sm", className: "text-base" })}
            >
              ورود
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            aria-label="راهنمای سایت"
            title="راهنمای سایت"
            onClick={startOnboardingTour}
          >
            <CircleHelp />
          </Button>
        </nav>
      </div>
    </header>
  );
}

export default SiteHeader;
