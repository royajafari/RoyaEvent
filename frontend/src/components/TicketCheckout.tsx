"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CompleteProfilePrompt } from "@/components/CompleteProfilePrompt";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatJalaliDateTime } from "@/lib/date";
import { ApiError, isIncompleteProfileError } from "@/lib/api-client";
import type { EventDetail, EventSessionOut } from "@/lib/events-api";
import type { MyTicket } from "@/lib/orders-api";
import { ordersApi } from "@/lib/orders-api";
import type { DiscountValidateResult, TicketType } from "@/lib/tickets-api";
import { ticketsApi } from "@/lib/tickets-api";
import { track } from "@/lib/track";
import { useAuthStore } from "@/store/auth-store";

const PRICING_LABELS: Record<TicketType["pricing_model"], string> = {
  free: "رایگان",
  paid: "پولی",
  donation: "حمایتی",
};

function formatPrice(ticket: TicketType) {
  if (ticket.pricing_model === "free") return "رایگان";
  return `${ticket.price.toLocaleString("fa-IR")} تومان`;
}

export function TicketCheckout({ event }: { event: EventDetail }) {
  const accessToken = useAuthStore((s) => s.accessToken);

  const [ticketTypes, setTicketTypes] = useState<TicketType[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(
    event.sessions[0]?.id ?? null,
  );
  const [discountCode, setDiscountCode] = useState("");
  const [discountResult, setDiscountResult] = useState<DiscountValidateResult | null>(null);
  const [discountError, setDiscountError] = useState<string | null>(null);
  const [checkingDiscount, setCheckingDiscount] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsProfile, setNeedsProfile] = useState(false);
  const [successCode, setSuccessCode] = useState<string | null>(null);
  const [existingTicket, setExistingTicket] = useState<MyTicket | null>(null);
  const [checkingExisting, setCheckingExisting] = useState(() => Boolean(accessToken));

  useEffect(() => {
    ticketsApi
      .listByEvent(event.id)
      .then((types) => {
        setTicketTypes(types);
        const firstAvailable = types.find((t) => !t.is_sold_out);
        setSelectedTicketId(firstAvailable?.id ?? types[0]?.id ?? null);
      })
      .catch(() => setError("خطا در دریافت نوع بلیط‌ها"))
      .finally(() => setLoadingTickets(false));
  }, [event.id]);

  useEffect(() => {
    if (!accessToken) return;
    ordersApi
      .myTickets(accessToken)
      .then((tickets) => {
        const found = tickets.find(
          (t) => t.registration.event_id === event.id && t.registration.status !== "cancelled",
        );
        setExistingTicket(found ?? null);
      })
      .catch(() => {})
      .finally(() => setCheckingExisting(false));
  }, [accessToken, event.id]);

  const selectedTicket = ticketTypes.find((t) => t.id === selectedTicketId) ?? null;

  async function handleCheckDiscount() {
    const trimmed = discountCode.trim();
    setDiscountResult(null);
    if (!trimmed) {
      setDiscountError("کد تخفیف معتبر نیست");
      return;
    }
    setDiscountError(null);
    setCheckingDiscount(true);
    try {
      const result = await ticketsApi.validateDiscount(trimmed, event.id);
      setDiscountResult(result);
    } catch (err) {
      setDiscountError(err instanceof ApiError ? err.message : "کد تخفیف معتبر نیست");
    } finally {
      setCheckingDiscount(false);
    }
  }

  async function handleSubmit() {
    if (!accessToken || !selectedTicketId || !selectedSessionId) return;
    track("funnel_step", { step: "CLICK_REGISTER", event_id: event.id });
    setSubmitting(true);
    setError(null);
    setNeedsProfile(false);
    try {
      track("funnel_step", { step: "START_CHECKOUT", event_id: event.id });
      const order = await ordersApi.create(
        {
          ticket_type_id: selectedTicketId,
          session_id: selectedSessionId,
          discount_code: discountCode || null,
        },
        accessToken,
      );
      await ordersApi.complete(order.id, accessToken);
      track("funnel_step", { step: "COMPLETE_ORDER", event_id: event.id });
      setSuccessCode(order.id.toString());
    } catch (err) {
      if (isIncompleteProfileError(err)) {
        setNeedsProfile(true);
      } else {
        setError(err instanceof ApiError ? err.message : "خطا در ثبت‌نام؛ دوباره تلاش کنید");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingTickets || checkingExisting) {
    return <p className="text-muted-foreground text-sm">در حال بارگذاری بلیط‌ها...</p>;
  }

  if (existingTicket && !successCode) {
    return (
      <Card id="ticket-checkout" className="border-primary text-right">
        <CardHeader>
          <CardTitle>شما قبلاً این بلیط را خریده‌اید ✓</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-muted-foreground text-sm">
            کد بلیط: <span className="font-mono">{existingTicket.registration.ticket_code}</span>
          </p>
          <Link href="/tickets" className={buttonVariants({ className: "w-fit" })}>
            مشاهده بلیط‌های من
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (ticketTypes.length === 0) {
    return <p className="text-muted-foreground text-sm">هنوز بلیطی برای این رویداد تعریف نشده است.</p>;
  }

  if (successCode) {
    return (
      <Card id="ticket-checkout" className="border-primary text-right">
        <CardHeader>
          <CardTitle>ثبت‌نام با موفقیت انجام شد 🎉</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-muted-foreground text-sm">
            بلیط شما صادر شد. می‌توانید جزئیات و لینک تقویم را در «بلیط‌های من» ببینید.
          </p>
          <Link href="/tickets" className={buttonVariants({ className: "w-fit" })}>
            مشاهده بلیط‌های من
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card id="ticket-checkout" className="text-right">
      <CardHeader>
        <CardTitle>انتخاب بلیط</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          {ticketTypes.map((ticket) => (
            <button
              key={ticket.id}
              type="button"
              disabled={ticket.is_sold_out || (ticket.is_early_bird && !ticket.is_early_bird_active)}
              onClick={() => setSelectedTicketId(ticket.id)}
              className={`flex items-center justify-between rounded-md border p-3 text-right transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                selectedTicketId === ticket.id ? "border-primary bg-primary/5" : "border-border"
              }`}
            >
              <span className="flex flex-col items-start gap-1">
                <span className="font-medium">{ticket.name}</span>
                <span className="flex gap-1">
                  <Badge variant="outline">{PRICING_LABELS[ticket.pricing_model]}</Badge>
                  {ticket.is_early_bird && (
                    <Badge variant={ticket.is_early_bird_active ? "default" : "secondary"}>
                      {ticket.is_early_bird_active ? "زودهنگام (فعال)" : "زودهنگام (پایان‌یافته)"}
                    </Badge>
                  )}
                  {ticket.is_sold_out && <Badge variant="destructive">تکمیل ظرفیت</Badge>}
                </span>
              </span>
              <span className="font-semibold">{formatPrice(ticket)}</span>
            </button>
          ))}
        </div>

        {event.sessions.length > 1 && (
          <div className="flex flex-col gap-2">
            <Label>جلسه</Label>
            <div className="flex flex-col gap-2">
              {event.sessions.map((session: EventSessionOut, index: number) => (
                <button
                  key={session.id}
                  type="button"
                  onClick={() => setSelectedSessionId(session.id)}
                  className={`rounded-md border p-2 text-right text-sm transition-colors ${
                    selectedSessionId === session.id ? "border-primary bg-primary/5" : "border-border"
                  }`}
                >
                  جلسه {index + 1} — {formatJalaliDateTime(session.starts_at)}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col gap-2">
          <Label htmlFor="discount">کد تخفیف (اختیاری)</Label>
          <div className="flex gap-2">
            <Input
              id="discount"
              dir="ltr"
              value={discountCode}
              onChange={(e) => {
                setDiscountCode(e.target.value);
                setDiscountResult(null);
                setDiscountError(null);
              }}
              placeholder="کد تخفیف خود را وارد کنید"
              className="flex-1"
            />
            <Button
              type="button"
              variant="outline"
              disabled={checkingDiscount}
              onClick={handleCheckDiscount}
            >
              {checkingDiscount ? "در حال بررسی..." : "بررسی کد"}
            </Button>
          </div>
          {discountError && <p className="text-destructive text-sm">{discountError}</p>}
          {discountResult && (
            <p className="text-primary text-sm">
              کد تخفیف معتبر است —{" "}
              {discountResult.discount_type === "percent"
                ? `${discountResult.value}٪ تخفیف`
                : `${discountResult.value.toLocaleString("fa-IR")} تومان تخفیف`}
            </p>
          )}
        </div>

        {error && <p className="text-destructive text-sm">{error}</p>}
        {needsProfile && (
          <CompleteProfilePrompt onCompleted={() => { setNeedsProfile(false); handleSubmit(); }} />
        )}

        {!accessToken ? (
          <Link href="/login" className={buttonVariants({ className: "w-full" })}>
            برای ثبت‌نام وارد شوید
          </Link>
        ) : (
          <Button
            disabled={submitting || !selectedTicket || !selectedSessionId || selectedTicket.is_sold_out}
            onClick={handleSubmit}
            className="w-full"
          >
            {submitting ? "در حال ثبت..." : "ثبت‌نام و دریافت بلیط"}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export default TicketCheckout;
