"use client";

import { useState } from "react";
import { Zap } from "lucide-react";

import { InstantRegisterModal } from "@/components/InstantRegisterModal";
import { Button } from "@/components/ui/button";
import type { EventListItem } from "@/lib/events-api";

// دکمه‌ی داخل EventCard (که خودش یه Link تمام‌کارته) — کلیک نباید باعث
// navigate شدن به صفحه‌ی جزئیات بشه، برای همین stopPropagation/preventDefault.
export function InstantRegisterButton({ event }: { event: EventListItem }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        size="sm"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setOpen(true);
        }}
        className="gap-1"
      >
        <Zap className="size-3.5" />
        ثبت‌نام فوری
      </Button>
      {open && <InstantRegisterModal event={event} onOpenChange={setOpen} />}
    </>
  );
}

export default InstantRegisterButton;
