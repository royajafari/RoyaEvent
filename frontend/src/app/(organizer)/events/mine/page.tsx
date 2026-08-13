"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api-client";
import type { EventListItem } from "@/lib/events-api";
import { eventsApi } from "@/lib/events-api";
import { useAuthStore } from "@/store/auth-store";

const STATUS_LABELS: Record<EventListItem["status"], string> = {
  draft: "پیش‌نویس",
  published: "منتشرشده",
  cancelled: "لغوشده",
};

export default function MyEventsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [events, setEvents] = useState<EventListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // بدون accessToken، برنچ رندر پایین (پیام «باید وارد شوید») نمایش داده
    // می‌شود و به loading اصلاً نیازی نیست؛ پس اینجا setState صدا نمی‌زنیم.
    if (!accessToken) {
      return;
    }
    eventsApi
      .listMine(accessToken)
      .then(setEvents)
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت رویدادها"))
      .finally(() => setLoading(false));
  }, [accessToken]);

  async function handlePublish(id: number) {
    if (!accessToken) return;
    try {
      await eventsApi.publish(id, accessToken);
      const refreshed = await eventsApi.listMine(accessToken);
      setEvents(refreshed);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در انتشار رویداد");
    }
  }

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن رویدادهای خودتان باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">رویدادهای من</h1>
        <Link href="/events/create" className={buttonVariants({ variant: "outline", size: "sm" })}>
          + رویداد جدید
        </Link>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}
      {!loading && events.length === 0 && (
        <p className="text-muted-foreground">هنوز رویدادی نساخته‌اید.</p>
      )}

      <div className="flex flex-col gap-3">
        {events.map((event) => (
          <Card key={event.id} className="text-right">
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="text-base">{event.title}</CardTitle>
              <Badge variant={event.status === "published" ? "default" : "secondary"}>
                {STATUS_LABELS[event.status]}
              </Badge>
            </CardHeader>
            <CardContent className="flex items-center gap-2">
              {event.status === "published" && (
                <>
                  <Link
                    href={`/events/${event.slug}`}
                    className={buttonVariants({ variant: "outline", size: "sm" })}
                  >
                    مشاهده صفحه‌ی عمومی
                  </Link>
                  <Link
                    href={`/organizer/events/${event.id}/attendees`}
                    className={buttonVariants({ variant: "outline", size: "sm" })}
                  >
                    شرکت‌کنندگان
                  </Link>
                </>
              )}
              {event.status === "draft" && (
                <Button size="sm" onClick={() => handlePublish(event.id)}>
                  انتشار
                </Button>
              )}
              <span className="text-muted-foreground text-xs">کد: {event.event_code}</span>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
