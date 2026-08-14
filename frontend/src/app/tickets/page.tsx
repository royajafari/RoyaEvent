"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
      <h1 className="text-2xl font-bold">بلیط‌های من</h1>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}
      {!loading && tickets.length === 0 && (
        <p className="text-muted-foreground">هنوز بلیطی ثبت نکرده‌اید.</p>
      )}

      <div className="flex flex-col gap-3">
        {tickets.map(({ registration, event_title, event_slug, session_starts_at }) => {
          // eslint-disable-next-line react-hooks/purity -- مقایسه با «اکنون» است، نه باگ
          const isPast = new Date(session_starts_at).getTime() < Date.now();
          return (
            <Card key={registration.id} className="text-right">
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">
                  <Link href={`/events/${event_slug}`} className="hover:underline">
                    {event_title}
                  </Link>
                </CardTitle>
                <div className="flex items-center gap-2">
                  {isPast && <Badge variant="secondary">این رویداد منقضی شده</Badge>}
                  <Badge variant={registration.status === "confirmed" ? "default" : "secondary"}>
                    {STATUS_LABELS[registration.status]}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-sm">
                  <span>زمان: {formatJalaliDateTime(session_starts_at)}</span>
                  <span dir="ltr">کد بلیط: {registration.ticket_code}</span>
                </div>
                <div className="flex items-center gap-2">
                  {registration.status === "confirmed" && (
                    <>
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
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
