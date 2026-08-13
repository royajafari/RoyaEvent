"use client";

import Link from "next/link";
import { CircleHelp } from "lucide-react";

import { RoyaEventLogo } from "@/components/RoyaEventLogo";
import { Button, buttonVariants } from "@/components/ui/button";
import { startOnboardingTour } from "@/lib/onboarding-tour";

export function SiteHeader() {
  return (
    <header className="border-border bg-background/95 sticky top-0 z-40 border-b backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
        <Link href="/" id="tour-logo" className="shrink-0">
          <RoyaEventLogo size={22} />
        </Link>
        <nav className="flex flex-wrap items-center gap-1 sm:gap-2">
          <Link
            href="/events"
            id="tour-events"
            className={buttonVariants({ variant: "ghost", size: "sm" })}
          >
            رویدادها
          </Link>
          <Link
            href="/events/mine"
            id="tour-mine"
            className={buttonVariants({ variant: "ghost", size: "sm" })}
          >
            رویدادهای من
          </Link>
          <Link
            href="/tickets"
            id="tour-tickets"
            className={buttonVariants({ variant: "ghost", size: "sm" })}
          >
            بلیط‌های من
          </Link>
          <Link
            href="/events/create"
            id="tour-create"
            className={buttonVariants({ variant: "ghost", size: "sm" })}
          >
            ایجاد رویداد
          </Link>
          <Link
            href="/login"
            id="tour-login"
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            ورود
          </Link>
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
