"use client";

import { useRef } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { EventCard } from "@/components/EventCard";
import type { EventListItem } from "@/lib/events-api";

const SCROLL_AMOUNT = 280;

export function EventCarousel({
  title,
  events,
  viewAllHref,
}: {
  title: string;
  events: EventListItem[];
  viewAllHref: string;
}) {
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  if (events.length === 0) return null;

  return (
    <section className="flex w-full max-w-6xl flex-col gap-4 px-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{title}</h2>
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
