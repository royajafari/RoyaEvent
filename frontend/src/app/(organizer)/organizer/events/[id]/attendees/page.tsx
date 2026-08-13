"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api-client";
import { formatJalaliDateTime } from "@/lib/date";
import type { EventDetail } from "@/lib/events-api";
import { eventsApi } from "@/lib/events-api";
import type { Attendee } from "@/lib/organizer-api";
import { organizerApi } from "@/lib/organizer-api";
import { useAuthStore } from "@/store/auth-store";

const STATUS_LABELS: Record<string, string> = {
  confirmed: "تأییدشده",
  cancelled: "لغوشده",
  checked_in: "حضور ثبت‌شده",
};

export default function AttendeesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const eventId = Number(id);
  const accessToken = useAuthStore((s) => s.accessToken);

  const [event, setEvent] = useState<EventDetail | null>(null);
  const [attendees, setAttendees] = useState<Attendee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    Promise.all([eventsApi.getById(eventId, accessToken), organizerApi.listAttendees(eventId, accessToken)])
      .then(([eventData, attendeeData]) => {
        setEvent(eventData);
        setAttendees(attendeeData);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت اطلاعات"))
      .finally(() => setLoading(false));
  }, [accessToken, eventId]);

  async function handleRemove(registrationId: number) {
    if (!accessToken) return;
    setBusyId(registrationId);
    try {
      const updated = await organizerApi.removeAttendee(eventId, registrationId, accessToken);
      setAttendees((prev) => prev.map((a) => (a.registration_id === registrationId ? updated : a)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در حذف شرکت‌کننده");
    } finally {
      setBusyId(null);
    }
  }

  async function handleExport() {
    if (!accessToken) return;
    setExporting(true);
    try {
      await organizerApi.downloadAttendeesCsv(eventId, accessToken);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در دریافت خروجی CSV");
    } finally {
      setExporting(false);
    }
  }

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن این صفحه باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">
          شرکت‌کنندگان {event ? `— ${event.title}` : ""}
        </h1>
        <Button variant="outline" size="sm" onClick={handleExport} disabled={exporting}>
          {exporting ? "در حال دریافت..." : "خروجی CSV"}
        </Button>
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}
      {!loading && attendees.length === 0 && (
        <p className="text-muted-foreground">هنوز شرکت‌کننده‌ای ثبت‌نام نکرده است.</p>
      )}

      <div className="flex flex-col gap-3">
        {attendees.map((attendee) => (
          <Card key={attendee.registration_id} className="text-right">
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="text-base">
                {attendee.user_full_name ?? "بدون نام"}
              </CardTitle>
              <Badge variant={attendee.status === "confirmed" ? "default" : "secondary"}>
                {STATUS_LABELS[attendee.status] ?? attendee.status}
              </Badge>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <div className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-sm">
                {attendee.user_phone && <span dir="ltr">{attendee.user_phone}</span>}
                {attendee.user_email && <span dir="ltr">{attendee.user_email}</span>}
                <span>نوع بلیط: {attendee.ticket_type_name}</span>
                <span>زمان جلسه: {formatJalaliDateTime(attendee.session_starts_at)}</span>
                <span dir="ltr">کد بلیط: {attendee.ticket_code}</span>
              </div>
              {attendee.status === "confirmed" && (
                <Button
                  size="sm"
                  variant="destructive"
                  className="w-fit"
                  disabled={busyId === attendee.registration_id}
                  onClick={() => handleRemove(attendee.registration_id)}
                >
                  حذف شرکت‌کننده
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
