"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api-client";
import type { MyFollowsDetail } from "@/lib/social-api";
import { socialApi } from "@/lib/social-api";
import { useAuthStore } from "@/store/auth-store";

export default function FollowsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [follows, setFollows] = useState<MyFollowsDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    socialApi
      .myFollowsDetail(accessToken)
      .then(setFollows)
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت دنبال‌کردن‌ها"))
      .finally(() => setLoading(false));
  }, [accessToken]);

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن دنبال‌کردن‌های خودتان باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  const hasNothing = follows && follows.organizers.length === 0 && follows.instructors.length === 0;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-10">
      <h1 className="text-2xl font-bold">دنبال‌کردن‌های من</h1>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}
      {hasNothing && (
        <p className="text-muted-foreground">
          هنوز هیچ برگزارکننده یا مدرسی رو دنبال نکردید — دکمه‌ی «دنبال کردن» تو صفحه‌ی هر رویداد یا مدرس هست.
        </p>
      )}

      {follows && follows.instructors.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">مدرس‌ها</h2>
          <div className="flex flex-col gap-2">
            {follows.instructors.map((instructor) => (
              <Link key={instructor.id} href={`/instructors/${instructor.id}`}>
                <Card className="text-right transition-shadow hover:shadow-md">
                  <CardHeader className="flex-row items-center gap-3 space-y-0">
                    <div className="bg-muted flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full">
                      {instructor.avatar_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={instructor.avatar_url}
                          alt={instructor.name}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <span className="text-muted-foreground text-sm">
                          {instructor.name.charAt(0)}
                        </span>
                      )}
                    </div>
                    <CardTitle className="text-base">{instructor.name}</CardTitle>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}

      {follows && follows.organizers.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">برگزارکننده‌ها</h2>
          <div className="flex flex-col gap-2">
            {follows.organizers.map((organizer) => (
              <Link key={organizer.id} href={`/organizers/${organizer.id}`}>
                <Card className="text-right transition-shadow hover:shadow-md">
                  <CardHeader className="flex-row items-center gap-3 space-y-0">
                    <div className="bg-muted flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full">
                      {organizer.avatar_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={organizer.avatar_url}
                          alt={organizer.name ?? "بدون نام"}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <span className="text-muted-foreground text-sm">
                          {(organizer.name ?? "؟").charAt(0)}
                        </span>
                      )}
                    </div>
                    <CardTitle className="text-base">{organizer.name ?? "بدون نام"}</CardTitle>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
