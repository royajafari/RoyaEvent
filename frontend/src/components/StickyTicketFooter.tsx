"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import type { EventDetail } from "@/lib/events-api";
import type { TicketType } from "@/lib/tickets-api";
import { ticketsApi } from "@/lib/tickets-api";

function cheapestLabel(ticketTypes: TicketType[]) {
  const available = ticketTypes.filter((t) => !t.is_sold_out);
  const pool = available.length > 0 ? available : ticketTypes;
  if (pool.length === 0) return null;
  const cheapest = pool.reduce((min, t) => (t.price < min.price ? t : min), pool[0]);
  if (cheapest.pricing_model === "free") return "رایگان";
  return `از ${cheapest.price.toLocaleString("fa-IR")} تومان`;
}

export function StickyTicketFooter({ event }: { event: EventDetail }) {
  const [ticketTypes, setTicketTypes] = useState<TicketType[]>([]);
  const [checkoutVisible, setCheckoutVisible] = useState(false);

  useEffect(() => {
    ticketsApi
      .listByEvent(event.id)
      .then(setTicketTypes)
      .catch(() => setTicketTypes([]));
  }, [event.id]);

  // وقتی خود بخش «انتخاب بلیط» (با دکمه‌ی واقعی «ثبت‌نام و دریافت بلیط»)
  // تو دید کاربره، این دکمه‌ی شناور رو مخفی می‌کنیم — وگرنه کلیک روش با
  // scrollIntoView به یه المنت از قبل قابل‌مشاهده هیچ اتفاق مرئی‌ای نداره
  // و کاربر فکر می‌کنه دکمه خرابه.
  useEffect(() => {
    const target = document.getElementById("ticket-checkout");
    if (!target) return;
    const observer = new IntersectionObserver(([entry]) => setCheckoutVisible(entry.isIntersecting), {
      threshold: 0.15,
    });
    observer.observe(target);
    return () => observer.disconnect();
  }, [ticketTypes]);

  if (event.status !== "published" || ticketTypes.length === 0 || checkoutVisible) return null;

  const priceLabel = cheapestLabel(ticketTypes);
  const soldOut = ticketTypes.every((t) => t.is_sold_out);

  return (
    <div className="bg-background/95 fixed inset-x-0 bottom-0 z-30 border-t backdrop-blur">
      <div className="mx-auto flex max-w-4xl items-center justify-between gap-3 px-4 py-4">
        <div className="flex min-w-0 flex-col gap-0.5">
          <span className="truncate text-sm font-semibold sm:text-base">{event.title}</span>
          <span className="text-base font-semibold sm:text-lg">
            {soldOut ? "ظرفیت تکمیل شده" : priceLabel}
          </span>
        </div>
        <Button
          size="lg"
          disabled={soldOut}
          onClick={() =>
            document.getElementById("ticket-checkout")?.scrollIntoView({ behavior: "smooth" })
          }
        >
          خرید بلیط
        </Button>
      </div>
    </div>
  );
}

export default StickyTicketFooter;
