"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Breadcrumbs } from "@/components/Breadcrumbs";
import { TicketQrCode } from "@/components/TicketQrCode";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import { formatJalaliDateTime, isSessionLive } from "@/lib/date";
import type { MyTicket } from "@/lib/orders-api";
import { ordersApi } from "@/lib/orders-api";
import { useAuthStore } from "@/store/auth-store";

const STATUS_LABELS: Record<MyTicket["registration"]["status"], string> = {
  confirmed: "تأییدشده",
  cancelled: "لغوشده",
  checked_in: "حضور ثبت‌شده",
};

export default function MyTicketsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [tickets, setTickets] = useState<MyTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  function loadTickets(token: string) {
    ordersApi
      .myTickets(token)
      .then(setTickets)
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت بلیط‌ها"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!accessToken) return;
    loadTickets(accessToken);
  }, [accessToken]);

  async function handleCancel(registrationId: number) {
    if (!accessToken) return;
    setBusyId(registrationId);
    try {
      await ordersApi.cancelRegistration(registrationId, accessToken);
      loadTickets(accessToken);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در لغو ثبت‌نام");
    } finally {
      setBusyId(null);
    }
  }

  async function handleCalendar(registrationId: number) {
    if (!accessToken) return;
    try {
      const { calendar_link } = await ordersApi.calendarLink(registrationId, accessToken);
      window.open(calendar_link, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در دریافت لینک تقویم");
    }
  }

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن بلیط‌های خودتان باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10">
      <Breadcrumbs items={[{ label: "بلیط‌های من" }]} />
      <h1 className="text-2xl font-bold">بلیط‌های من</h1>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}
      {!loading && tickets.length === 0 && (
        <p className="text-muted-foreground">هنوز بلیطی ثبت نکرده‌اید.</p>
      )}

      {tickets.length > 0 && (
        <div className="bg-card overflow-x-auto rounded-lg ring-1 ring-foreground/10">
          {/* table-layout:fixed + عرض درصدی روی هر ستون، تا محتوا و دکمه‌ها
              مجبور به wrap داخل همون ستون بشن، نه این‌که کل جدول رو بازم
              (table-layout پیش‌فرض auto فقط با حذف whitespace-nowrap عرض
              ستون رو به‌اندازه‌ی محتوای بازنشده بزرگ نگه می‌داشت). */}
          <table className="w-full table-fixed text-right text-sm">
            <thead className="bg-muted/50 text-muted-foreground text-xs">
              <tr>
                <th className="w-[16%] px-3 py-2 font-normal">رویداد</th>
                <th className="w-[12%] px-3 py-2 font-normal">وضعیت</th>
                <th className="w-[15%] px-3 py-2 font-normal">زمان</th>
                <th className="w-[15%] px-3 py-2 font-normal">محل/لینک</th>
                <th className="w-[12%] px-3 py-2 font-normal">کد بلیط</th>
                <th className="w-[30%] px-3 py-2 font-normal">عملیات</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map(
                ({
                  registration,
                  event_title,
                  event_slug,
                  event_format,
                  session_starts_at,
                  session_duration_minutes,
                  session_online_join_url,
                  session_venue_address,
                }) => {
                const sessionEnd =
                  new Date(session_starts_at).getTime() + session_duration_minutes * 60 * 1000;
                // eslint-disable-next-line react-hooks/purity -- مقایسه با «اکنون» است، نه باگ
                const isEnded = Date.now() > sessionEnd;
                const isLive = isSessionLive(session_starts_at, session_duration_minutes);
                return (
                  <tr key={registration.id} className="border-border border-t align-top">
                    <td className="px-3 py-2 break-words">
                      <Link href={`/events/${event_slug}`} className="font-medium hover:underline">
                        {event_title}
                      </Link>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <Badge variant={registration.status === "confirmed" ? "default" : "secondary"}>
                          {STATUS_LABELS[registration.status]}
                        </Badge>
                        {isLive && <Badge variant="destructive">در حال ارائه</Badge>}
                        {!isLive && isEnded && <Badge variant="secondary">منقضی‌شده</Badge>}
                      </div>
                    </td>
                    <td className="text-muted-foreground px-3 py-2 break-words">
                      {formatJalaliDateTime(session_starts_at)}
                    </td>
                    <td className="px-3 py-2 break-words">
                      {event_format !== "in_person" && session_online_join_url ? (
                        <a
                          href={session_online_join_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          ورود به جلسه
                        </a>
                      ) : event_format !== "in_person" ? (
                        <span className="text-muted-foreground text-xs">لینک هنوز اعلام نشده</span>
                      ) : (
                        <span className="text-muted-foreground text-xs">
                          {session_venue_address ?? "—"}
                        </span>
                      )}
                    </td>
                    <td className="text-muted-foreground px-3 py-2 break-all" dir="ltr">
                      {registration.ticket_code}
                    </td>
                    <td className="px-3 py-2">
                      {registration.status === "confirmed" && (
                        <div className="flex flex-wrap gap-1.5">
                          <TicketQrCode
                            ticketCode={registration.ticket_code}
                            eventId={registration.event_id}
                          />
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleCalendar(registration.id)}
                          >
                            افزودن به تقویم
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            disabled={busyId === registration.id}
                            onClick={() => handleCancel(registration.id)}
                          >
                            لغو ثبت‌نام
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
