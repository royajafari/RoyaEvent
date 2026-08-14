"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Breadcrumbs } from "@/components/Breadcrumbs";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api-client";
import type { FollowerUser, MyFollowers } from "@/lib/social-api";
import { socialApi } from "@/lib/social-api";
import { useAuthStore } from "@/store/auth-store";

function FollowerCard({ follower }: { follower: FollowerUser }) {
  return (
    <Card className="text-right">
      <CardHeader className="flex-row items-center gap-3 space-y-0">
        <div className="bg-muted flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full">
          {follower.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={follower.avatar_url}
              alt={follower.name ?? "بدون نام"}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-muted-foreground text-sm">
              {(follower.name ?? "؟").charAt(0)}
            </span>
          )}
        </div>
        <CardTitle className="text-base">{follower.name ?? "بدون نام"}</CardTitle>
      </CardHeader>
    </Card>
  );
}

export default function FollowersPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [followers, setFollowers] = useState<MyFollowers | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    socialApi
      .myFollowers(accessToken)
      .then(setFollowers)
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت دنبال‌کنندگان"))
      .finally(() => setLoading(false));
  }, [accessToken]);

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن دنبال‌کنندگان خودتان باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  const hasNothing =
    followers && followers.as_organizer.length === 0 && followers.as_instructor.length === 0;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-10">
      <Breadcrumbs items={[{ label: "دنبال‌کنندگان من" }]} />
      <h1 className="text-2xl font-bold">دنبال‌کنندگان من</h1>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}
      {hasNothing && (
        <p className="text-muted-foreground">
          هنوز کسی شما رو دنبال نکرده. اگه پروفایل مدرس خودتون رو claim نکردید، از صفحه‌ی عمومی
          مدرس روی «این پروفایل منم» بزنید تا دنبال‌کننده‌های اون‌جا هم اینجا دیده بشن.
        </p>
      )}

      {followers && followers.as_organizer.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">دنبال‌کننده‌های من به‌عنوان برگزارکننده</h2>
          <div className="flex flex-col gap-2">
            {followers.as_organizer.map((follower) => (
              <FollowerCard key={follower.id} follower={follower} />
            ))}
          </div>
        </section>
      )}

      {followers && followers.as_instructor.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">دنبال‌کننده‌های من به‌عنوان مدرس</h2>
          <div className="flex flex-col gap-2">
            {followers.as_instructor.map((follower) => (
              <FollowerCard key={follower.id} follower={follower} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
