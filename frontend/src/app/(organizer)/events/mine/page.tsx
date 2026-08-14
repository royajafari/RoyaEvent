"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
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
  const [publishingId, setPublishingId] = useState<number | null>(null);

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
    if (!accessToken || publishingId !== null) return;
    setPublishingId(id);
    setError(null);
    try {
      await eventsApi.publish(id, accessToken);
      const refreshed = await eventsApi.listMine(accessToken);
      setEvents(refreshed);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در انتشار رویداد");
    } finally {
      setPublishingId(null);
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
      <Breadcrumbs items={[{ label: "رویدادهای من" }]} />
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

      {events.length > 0 && (
        <div className="bg-card overflow-x-auto rounded-lg ring-1 ring-foreground/10">
          <table className="w-full text-right text-sm">
            <thead className="bg-muted/50 text-muted-foreground text-xs">
              <tr>
                <th className="px-3 py-2 font-normal">عنوان</th>
                <th className="px-3 py-2 font-normal">وضعیت</th>
                <th className="px-3 py-2 font-normal">کد</th>
                <th className="px-3 py-2 font-normal">عملیات</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id} className="border-border border-t">
                  <td className="px-3 py-2 font-medium">{event.title}</td>
                  <td className="px-3 py-2">
                    <Badge variant={event.status === "published" ? "default" : "secondary"}>
                      {STATUS_LABELS[event.status]}
                    </Badge>
                  </td>
                  <td className="text-muted-foreground px-3 py-2 whitespace-nowrap">
                    {event.event_code}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-nowrap gap-1.5">
                      {event.status === "published" && (
                        <>
                          <Link
                            href={`/events/${event.slug}`}
                            className={buttonVariants({
                              variant: "outline",
                              size: "sm",
                              className: "whitespace-nowrap",
                            })}
                          >
                            مشاهده صفحه‌ی عمومی
                          </Link>
                          <Link
                            href={`/organizer/events/${event.id}/attendees`}
                            className={buttonVariants({
                              variant: "outline",
                              size: "sm",
                              className: "whitespace-nowrap",
                            })}
                          >
                            شرکت‌کنندگان
                          </Link>
                        </>
                      )}
                      {event.status === "draft" && (
                        <Button
                          size="sm"
                          className="whitespace-nowrap"
                          disabled={publishingId !== null}
                          onClick={() => handlePublish(event.id)}
                        >
                          {publishingId === event.id ? "در حال انتشار..." : "انتشار"}
                        </Button>
                      )}
                      <Link
                        href={`/organizer/events/${event.id}/tickets`}
                        className={buttonVariants({
                          variant: "outline",
                          size: "sm",
                          className: "whitespace-nowrap",
                        })}
                      >
                        بلیط‌ها
                      </Link>
                      <Link
                        href={`/organizer/events/${event.id}/edit`}
                        className={buttonVariants({
                          variant: "outline",
                          size: "sm",
                          className: "whitespace-nowrap",
                        })}
                      >
                        ویرایش
                      </Link>
                      <Link
                        href={`/organizer/events/${event.id}/media`}
                        className={buttonVariants({
                          variant: "outline",
                          size: "sm",
                          className: "whitespace-nowrap",
                        })}
                      >
                        بنر و کلیپ
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
