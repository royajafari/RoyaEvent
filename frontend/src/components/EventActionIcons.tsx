"use client";

import { useState } from "react";
import { CalendarPlus, Check, Link2 } from "lucide-react";

import { buildGoogleCalendarLink } from "@/lib/calendar";

export function EventActionIcons({
  title,
  description,
  location,
  startsAtIso,
  durationMinutes,
}: {
  title: string;
  description: string;
  location: string;
  startsAtIso: string | null;
  durationMinutes: number;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // کلیپ‌بورد در دسترس نبود (مرورگر/کانتکست ناامن) — بی‌صدا رد می‌شیم
    }
  }

  return (
    <div className="flex items-center gap-1.5">
      {startsAtIso && (
        <a
          href={buildGoogleCalendarLink({ title, description, location, startsAtIso, durationMinutes })}
          target="_blank"
          rel="noopener noreferrer"
          title="افزودن به تقویم گوگل"
          className="text-muted-foreground hover:bg-muted hover:text-foreground flex h-9 w-9 items-center justify-center rounded-full transition-colors"
        >
          <CalendarPlus className="h-4 w-4" />
        </a>
      )}
      <div className="relative">
        <button
          type="button"
          onClick={handleCopyLink}
          title="کپی لینک رویداد"
          className="text-muted-foreground hover:bg-muted hover:text-foreground flex h-9 w-9 items-center justify-center rounded-full transition-colors"
        >
          {copied ? <Check className="h-4 w-4 text-primary" /> : <Link2 className="h-4 w-4" />}
        </button>
        {copied && (
          <span className="bg-primary text-primary-foreground absolute top-full right-1/2 z-10 mt-1.5 translate-x-1/2 rounded-md px-2 py-1 text-xs whitespace-nowrap shadow">
            لینک کپی شد
          </span>
        )}
      </div>
    </div>
  );
}

export default EventActionIcons;
