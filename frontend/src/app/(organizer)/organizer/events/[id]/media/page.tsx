"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { ApiError } from "@/lib/api-client";
import type { EventDetail } from "@/lib/events-api";
import { eventsApi } from "@/lib/events-api";
import { useAuthStore } from "@/store/auth-store";

// ویرایش بنر/کلیپ برای رویدادی که قبلاً ساخته شده — چه پیش‌نویس چه
// منتشرشده. جدا از مرحله‌ی آپلود موقع ایجاد رویداد (create/page.tsx) چون
// کاربر ممکنه اون مرحله رو رد کرده باشه و بعداً بخواد اضافه/جایگزین کنه.
export default function EventMediaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const eventId = Number(id);
  const accessToken = useAuthStore((s) => s.accessToken);

  const [event, setEvent] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bannerProgress, setBannerProgress] = useState<number | null>(null);
  const [videoProgress, setVideoProgress] = useState<number | null>(null);
  const [bannerFileName, setBannerFileName] = useState<string | null>(null);
  const [videoFileName, setVideoFileName] = useState<string | null>(null);
  const bannerInputRef = useRef<HTMLInputElement | null>(null);
  const videoInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    eventsApi
      .getById(eventId, accessToken)
      .then(setEvent)
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت رویداد"))
      .finally(() => setLoading(false));
  }, [accessToken, eventId]);

  async function handleBannerUpload(file: File) {
    if (!accessToken) return;
    setError(null);
    setBannerFileName(file.name);
    setBannerProgress(0);
    try {
      const updated = await eventsApi.uploadBanner(eventId, file, accessToken, setBannerProgress);
      setEvent(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در آپلود بنر");
    } finally {
      setBannerProgress(null);
    }
  }

  async function handlePromoVideoUpload(file: File) {
    if (!accessToken) return;
    setError(null);
    setVideoFileName(file.name);
    setVideoProgress(0);
    try {
      const updated = await eventsApi.uploadPromoVideo(eventId, file, accessToken, setVideoProgress);
      setEvent(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در آپلود کلیپ");
    } finally {
      setVideoProgress(null);
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
      <Card className="text-right">
        <CardHeader>
          <CardTitle>بنر و کلیپ تبلیغاتی{event ? ` — ${event.title}` : ""}</CardTitle>
          <CardDescription>
            هر وقت خواستید می‌تونید بنر یا کلیپ رویداد رو اضافه یا جایگزین کنید — چه
            رویداد هنوز پیش‌نویس باشه چه قبلاً منتشر شده باشه.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}

          {event && (
            <>
              <div className="flex flex-col gap-2">
                <Label htmlFor="banner">بنر رویداد</Label>
                <input
                  ref={bannerInputRef}
                  id="banner"
                  type="file"
                  className="hidden"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(e) => e.target.files?.[0] && handleBannerUpload(e.target.files[0])}
                />
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => bannerInputRef.current?.click()}
                  >
                    {event.banner_url ? "جایگزینی بنر" : "انتخاب فایل بنر"}
                  </Button>
                  <span className="text-muted-foreground truncate text-sm">
                    {bannerFileName ?? "هنوز فایلی انتخاب نشده"}
                  </span>
                </div>
                {bannerProgress !== null && (
                  <div className="flex items-center gap-2">
                    <Progress value={bannerProgress} className="flex-1" />
                    <span className="text-muted-foreground text-xs">{bannerProgress}٪</span>
                  </div>
                )}
                {event.banner_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={event.banner_url}
                    alt="بنر رویداد"
                    className="aspect-video w-full rounded-md object-cover"
                  />
                )}
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="promo-video">
                  کلیپ کوتاه تبلیغاتی (حداکثر ۳۰ مگابایت، MP4/WebM)
                </Label>
                <input
                  ref={videoInputRef}
                  id="promo-video"
                  type="file"
                  className="hidden"
                  accept="video/mp4,video/webm"
                  onChange={(e) => e.target.files?.[0] && handlePromoVideoUpload(e.target.files[0])}
                />
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => videoInputRef.current?.click()}
                  >
                    {event.promo_video_url ? "جایگزینی کلیپ" : "انتخاب فایل کلیپ"}
                  </Button>
                  <span className="text-muted-foreground truncate text-sm">
                    {videoFileName ?? "هنوز فایلی انتخاب نشده"}
                  </span>
                </div>
                {videoProgress !== null && (
                  <div className="flex items-center gap-2">
                    <Progress value={videoProgress} className="flex-1" />
                    <span className="text-muted-foreground text-xs">{videoProgress}٪</span>
                  </div>
                )}
                {event.promo_video_url && (
                  <video
                    controls
                    preload="metadata"
                    src={event.promo_video_url}
                    className="aspect-video w-full rounded-md bg-black"
                  />
                )}
              </div>
            </>
          )}

          {error && <p className="text-destructive text-sm">{error}</p>}

          <Link href="/events/mine" className={buttonVariants({ variant: "outline" })}>
            بازگشت به رویدادهای من
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
