"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import { formatJalaliDateTime } from "@/lib/date";
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
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-10">
      <Breadcrumbs items={[{ label: "بلیط‌های من" }]} />
      <h1 className="text-2xl font-bold">بلیط‌های من</h1>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}
      {!loading && tickets.length === 0 && (
        <p className="text-muted-foreground">هنوز بلیطی ثبت نکرده‌اید.</p>
      )}

      {tickets.length > 0 && (
        <div className="bg-card overflow-x-auto rounded-lg ring-1 ring-foreground/10">
          <table className="w-full text-right text-sm">
            <thead className="bg-muted/50 text-muted-foreground text-xs">
              <tr>
                <th className="px-3 py-2 font-normal">رویداد</th>
                <th className="px-3 py-2 font-normal">وضعیت</th>
                <th className="px-3 py-2 font-normal">زمان</th>
                <th className="px-3 py-2 font-normal">کد بلیط</th>
                <th className="px-3 py-2 font-normal">عملیات</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map(({ registration, event_title, event_slug, session_starts_at }) => {
                // eslint-disable-next-line react-hooks/purity -- مقایسه با «اکنون» است، نه باگ
                const isPast = new Date(session_starts_at).getTime() < Date.now();
                return (
                  <tr key={registration.id} className="border-border border-t">
                    <td className="px-3 py-2">
                      <Link href={`/events/${event_slug}`} className="font-medium hover:underline">
                        {event_title}
                      </Link>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <Badge variant={registration.status === "confirmed" ? "default" : "secondary"}>
                          {STATUS_LABELS[registration.status]}
                        </Badge>
                        {isPast && <Badge variant="secondary">منقضی‌شده</Badge>}
                      </div>
                    </td>
                    <td className="text-muted-foreground px-3 py-2 whitespace-nowrap">
                      {formatJalaliDateTime(session_starts_at)}
                    </td>
                    <td className="text-muted-foreground px-3 py-2" dir="ltr">
                      {registration.ticket_code}
                    </td>
                    <td className="px-3 py-2">
                      {registration.status === "confirmed" && (
                        <div className="flex flex-nowrap gap-1.5">
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
