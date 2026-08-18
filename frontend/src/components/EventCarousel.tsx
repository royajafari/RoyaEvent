"use client";

import { useRef } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Heart, Star } from "lucide-react";

import { EventCard } from "@/components/EventCard";
import type { EventListItem } from "@/lib/events-api";

const SCROLL_AMOUNT = 280;

export function EventCarousel({
  title,
  events,
  viewAllHref,
  highlight = false,
  pulseIcon,
  id,
}: {
  title: string;
  events: EventListItem[];
  viewAllHref: string;
  /** برای بخش‌هایی مثل «وبینارهای پیش‌رو» — پس‌زمینه‌ی صورتی کنار عنوان،
   * برای جلب توجه به رویدادهایی که به‌زودی/همین الان برگزار می‌شن. */
  highlight?: boolean;
  /** نشان چشمک‌زن کنار عنوان، مستقل از highlight — "dot" برای پیش‌رو (نشون
   * دادن زنده‌بودن)، "heart" برای محبوب (نشون دادن پرطرفدار بودن)، "star"
   * برای ویژه (نشون دادن انتخاب‌شده بودن). */
  pulseIcon?: "dot" | "heart" | "star";
  /** برای هدف‌گیری تور آموزشی سایت (lib/onboarding-tour.ts) روی بخش‌های
   * خاص صفحه‌ی اصلی — اختیاریه چون این کامپوننت چندبار با title متفاوت
   * تو یک صفحه استفاده می‌شه. */
  id?: string;
}) {
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  if (events.length === 0) return null;

  return (
    <section
      id={id}
      className={`flex w-full max-w-6xl flex-col gap-4 px-4 ${
        highlight ? "bg-destructive/10 rounded-xl py-6" : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          {pulseIcon === "dot" && (
            <span className="relative flex h-3 w-3">
              <span className="bg-destructive absolute inline-flex h-full w-full animate-ping rounded-full opacity-75" />
              <span className="bg-destructive relative inline-flex h-3 w-3 rounded-full" />
            </span>
          )}
          {pulseIcon === "heart" && (
            <Heart className="fill-destructive text-destructive h-4 w-4 animate-pulse" />
          )}
          {pulseIcon === "star" && (
            <Star className="fill-primary text-primary h-4 w-4 animate-pulse" />
          )}
          {title}
        </h2>
        <Link
          href={viewAllHref}
          className="text-primary flex items-center gap-1 text-sm hover:underline"
        >
          مشاهده همه
          <ChevronLeft className="size-4" />
        </Link>
      </div>
      <div className="relative">
        <div
          ref={scrollerRef}
          className="flex gap-4 overflow-x-auto scroll-smooth pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {events.map((event) => (
            <div key={event.id} className="w-60 shrink-0 sm:w-64">
              <EventCard event={event} />
            </div>
          ))}
        </div>
        {/* در مرورگرهای مدرن (Chrome/Firefox/Edge) موقع dir=rtl، مقدار
        scrollLeft منفی می‌شه ولی جهت مثبت/منفی scrollBy همیشه فیزیکیه
        (مثبت = راست، منفی = چپ) — مستقل از rtl/ltr؛ سافاری تاریخاً این
        قرارداد رو رعایت نمی‌کنه (محدودیت شناخته‌شده، نه باگ این کامپوننت). */}
        <button
          type="button"
          aria-label="نمایش موارد قبلی"
          onClick={() => scrollerRef.current?.scrollBy({ left: SCROLL_AMOUNT, behavior: "smooth" })}
          className="bg-background hover:bg-muted absolute top-1/2 right-0 z-10 -translate-y-1/2 translate-x-1/2 rounded-full border p-1.5 shadow-md"
        >
          <ChevronRight className="size-4" />
        </button>
        <button
          type="button"
          aria-label="نمایش موارد بعدی"
          onClick={() => scrollerRef.current?.scrollBy({ left: -SCROLL_AMOUNT, behavior: "smooth" })}
          className="bg-background hover:bg-muted absolute top-1/2 left-0 z-10 -translate-y-1/2 -translate-x-1/2 rounded-full border p-1.5 shadow-md"
        >
          <ChevronLeft className="size-4" />
        </button>
      </div>
    </section>
  );
}

export default EventCarousel;
