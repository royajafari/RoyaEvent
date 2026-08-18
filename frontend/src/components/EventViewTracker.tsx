"use client";

import { useEffect } from "react";

import { track } from "@/lib/track";

// بدون UI — قدم اول قیف (VIEW_EVENT) رو فقط برای صفحه‌ی جزئیات رویداد
// ثبت می‌کنه؛ جدا از PageViewTracker عمومی چون funnel_events یک کالکشن
// جدای Mongo با معنای دیگه‌ست (بخش ۱۱ پلن معماری).
export function EventViewTracker({ eventId }: { eventId: number }) {
  useEffect(() => {
    track("funnel_step", { step: "VIEW_EVENT", event_id: eventId });
  }, [eventId]);

  return null;
}

export default EventViewTracker;
