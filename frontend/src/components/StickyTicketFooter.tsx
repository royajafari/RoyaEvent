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

  useEffect(() => {
    ticketsApi
      .listByEvent(event.id)
      .then(setTicketTypes)
      .catch(() => setTicketTypes([]));
  }, [event.id]);

  if (event.status !== "published" || ticketTypes.length === 0) return null;

  const priceLabel = cheapestLabel(ticketTypes);
  const soldOut = ticketTypes.every((t) => t.is_sold_out);

  return (
    <div className="bg-background/95 fixed inset-x-0 bottom-0 z-30 border-t backdrop-blur">
      <div className="mx-auto flex max-w-4xl items-center justify-between gap-3 px-4 py-3">
        <div className="flex flex-col">
          <span className="text-muted-foreground text-xs">قیمت بلیط</span>
          <span className="font-semibold">{soldOut ? "ظرفیت تکمیل شده" : priceLabel}</span>
        </div>
        <Button
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
