import Link from "next/link";

import { RoyaEventLogo } from "@/components/RoyaEventLogo";
import { buttonVariants } from "@/components/ui/button";

export function SiteHeader() {
  return (
    <header className="border-border bg-background/95 sticky top-0 z-40 border-b backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
        <Link
          href="/"
          className="shrink-0 rounded-md px-3 py-1.5"
          style={{ backgroundColor: "var(--brand-dark)" }}
        >
          <RoyaEventLogo size={22} />
        </Link>
        <nav className="flex flex-wrap items-center gap-1 sm:gap-2">
          <Link href="/events" className={buttonVariants({ variant: "ghost", size: "sm" })}>
            رویدادها
          </Link>
          <Link href="/events/mine" className={buttonVariants({ variant: "ghost", size: "sm" })}>
            رویدادهای من
          </Link>
          <Link href="/tickets" className={buttonVariants({ variant: "ghost", size: "sm" })}>
            بلیط‌های من
          </Link>
          <Link href="/events/create" className={buttonVariants({ variant: "ghost", size: "sm" })}>
            ایجاد رویداد
          </Link>
          <Link href="/login" className={buttonVariants({ variant: "outline", size: "sm" })}>
            ورود
          </Link>
        </nav>
      </div>
    </header>
  );
}

export default SiteHeader;
