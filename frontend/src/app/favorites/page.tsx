"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Breadcrumbs } from "@/components/Breadcrumbs";
import { EventCard } from "@/components/EventCard";
import { buttonVariants } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import type { EventListItem } from "@/lib/events-api";
import { socialApi } from "@/lib/social-api";
import { useAuthStore } from "@/store/auth-store";

export default function FavoritesPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [events, setEvents] = useState<EventListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    socialApi
      .myFavorites(accessToken)
      .then(setEvents)
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت علاقه‌مندی‌ها"))
      .finally(() => setLoading(false));
  }, [accessToken]);

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن علاقه‌مندی‌های خودتان باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10">
      <Breadcrumbs items={[{ label: "علاقه‌مندی‌های من" }]} />
      <h1 className="text-2xl font-bold">علاقه‌مندی‌های من</h1>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}
      {!loading && events.length === 0 && (
        <p className="text-muted-foreground">
          هنوز رویدادی رو علاقه‌مند نکردید — با دکمه‌ی «افزودن به علاقه‌مندی‌ها» تو صفحه‌ی هر رویداد این کار رو انجام بدید.
        </p>
      )}

      {events.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      )}
    </div>
  );
}
