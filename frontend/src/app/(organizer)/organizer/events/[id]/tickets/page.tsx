"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ApiError } from "@/lib/api-client";
import type { EventDetail } from "@/lib/events-api";
import { eventsApi } from "@/lib/events-api";
import type { TicketType } from "@/lib/tickets-api";
import { ticketsApi } from "@/lib/tickets-api";
import { useAuthStore } from "@/store/auth-store";

const PRICING_LABELS: Record<TicketType["pricing_model"], string> = {
  free: "رایگان",
  paid: "پولی",
  donation: "حمایتی",
};

export default function EventTicketsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const eventId = Number(id);
  const accessToken = useAuthStore((s) => s.accessToken);

  const [event, setEvent] = useState<EventDetail | null>(null);
  const [ticketTypes, setTicketTypes] = useState<TicketType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState("");
  const [pricingModel, setPricingModel] = useState<TicketType["pricing_model"]>("free");
  const [price, setPrice] = useState("0");
  const [quantityTotal, setQuantityTotal] = useState("");
  const [isEarlyBird, setIsEarlyBird] = useState(false);

  const loadData = useCallback(
    (token: string) => {
      Promise.all([eventsApi.getById(eventId, token), ticketsApi.listByEvent(eventId)])
        .then(([eventData, types]) => {
          setEvent(eventData);
          setTicketTypes(types);
        })
        .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت اطلاعات"))
        .finally(() => setLoading(false));
    },
    [eventId],
  );

  useEffect(() => {
    if (!accessToken) return;
    loadData(accessToken);
  }, [accessToken, loadData]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    setError(null);
    setSubmitting(true);
    try {
      await ticketsApi.create(
        eventId,
        {
          name,
          pricing_model: pricingModel,
          price: pricingModel === "paid" ? Number(price) : 0,
          quantity_total: quantityTotal ? Number(quantityTotal) : null,
          is_early_bird: isEarlyBird,
        },
        accessToken,
      );
      setName("");
      setPrice("0");
      setQuantityTotal("");
      setIsEarlyBird(false);
      loadData(accessToken);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ایجاد نوع بلیط");
    } finally {
      setSubmitting(false);
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
    <div className="mx-auto flex max-w-xl flex-col gap-6 px-4 py-10">
      <div>
        <h1 className="text-2xl font-bold">انواع بلیط{event ? ` — ${event.title}` : ""}</h1>
        <p className="text-muted-foreground text-sm">
          بدون حداقل یک نوع بلیط، خریداران هیچ گزینه‌ای برای ثبت‌نام تو صفحه‌ی رویداد نمی‌بینن.
        </p>
      </div>

      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}

      {!loading && ticketTypes.length > 0 && (
        <div className="flex flex-col gap-2">
          {ticketTypes.map((t) => (
            <Card key={t.id} className="text-right">
              <CardContent className="flex items-center justify-between py-3">
                <div className="flex flex-col">
                  <span className="font-medium">{t.name}</span>
                  <span className="text-muted-foreground text-xs">
                    {t.pricing_model === "paid" ? `${t.price.toLocaleString("fa-IR")} تومان` : "رایگان"}
                    {t.quantity_total ? ` — ظرفیت ${t.quantity_total}` : ""}
                  </span>
                </div>
                <Badge variant="outline">{PRICING_LABELS[t.pricing_model]}</Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card className="text-right">
        <CardHeader>
          <CardTitle>افزودن نوع بلیط جدید</CardTitle>
          <CardDescription>مثلاً «بلیط عادی» یا «بلیط VIP»</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="ticket-name">نام بلیط</Label>
              <Input id="ticket-name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>

            <div className="flex flex-col gap-2">
              <Label>نوع قیمت‌گذاری</Label>
              <Select
                value={pricingModel}
                onValueChange={(v) => v && setPricingModel(v as TicketType["pricing_model"])}
              >
                <SelectTrigger className="w-full">
                  <SelectValue>{(v: string) => PRICING_LABELS[v as TicketType["pricing_model"]] ?? v}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="free">رایگان</SelectItem>
                  <SelectItem value="paid">پولی</SelectItem>
                  <SelectItem value="donation">حمایتی</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {pricingModel === "paid" && (
              <div className="flex flex-col gap-2">
                <Label htmlFor="price">قیمت (تومان)</Label>
                <Input
                  id="price"
                  type="number"
                  min={0}
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="flex flex-col gap-2">
              <Label htmlFor="quantity">ظرفیت (اختیاری، خالی = نامحدود)</Label>
              <Input
                id="quantity"
                type="number"
                min={1}
                value={quantityTotal}
                onChange={(e) => setQuantityTotal(e.target.value)}
              />
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={isEarlyBird}
                onChange={(e) => setIsEarlyBird(e.target.checked)}
              />
              بلیط زودهنگام (early-bird)
            </label>

            {error && <p className="text-destructive text-sm">{error}</p>}

            <Button type="submit" disabled={submitting || !name}>
              {submitting ? "در حال ثبت..." : "افزودن نوع بلیط"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Link href="/events/mine" className={buttonVariants({ variant: "outline" })}>
        بازگشت به رویدادهای من
      </Link>
    </div>
  );
}
