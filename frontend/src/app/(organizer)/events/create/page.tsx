"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Combobox,
  ComboboxCollection,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxGroupLabel,
  ComboboxInput,
  ComboboxInputGroup,
  ComboboxItem,
  ComboboxList,
  ComboboxTrigger,
} from "@/components/ui/combobox";
import { Input } from "@/components/ui/input";
import { JalaliDateTimePicker } from "@/components/JalaliDateTimePicker";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client";
import type { CategoryOut, EventDetail, EventSessionInput } from "@/lib/events-api";
import { eventsApi } from "@/lib/events-api";
import { useAuthStore } from "@/store/auth-store";

type SessionRow = { starts_at: string; duration_minutes: number };

// Base UI's Select.Value (برخلاف Radix) به‌صورت پیش‌فرض فقط raw value رو نشون
// می‌ده، نه لیبل آیتم متناظرش — باید صریحاً یه children (تابع) بهش بدیم که
// value رو به لیبل نمایشی نگاشت کنه.
const FORMAT_LABELS: Record<string, string> = {
  online: "آنلاین",
  in_person: "حضوری",
  hybrid: "ترکیبی",
};

const VISIBILITY_LABELS: Record<string, string> = {
  public: "عمومی",
  private: "خصوصی (فقط با لینک دعوت)",
};

function groupCategories(categories: CategoryOut[]) {
  const parents = categories.filter((c) => c.parent_id === null);
  return parents.map((parent) => ({
    parent,
    children: categories.filter((c) => c.parent_id === parent.id),
  }));
}

type CategoryComboboxItem = { value: string; label: string };

function buildCategoryComboboxGroups(categories: CategoryOut[]) {
  return groupCategories(categories).map(({ parent, children }) => ({
    label: parent.name,
    items: children.map((child): CategoryComboboxItem => ({
      value: String(child.id),
      label: child.name,
    })),
  }));
}

export default function CreateEventPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);

  const [categories, setCategories] = useState<CategoryOut[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState<string>("");
  const [format, setFormat] = useState<"online" | "in_person" | "hybrid">("online");
  const [venueAddress, setVenueAddress] = useState("");
  const [onlinePlatform, setOnlinePlatform] = useState("");
  const [visibility, setVisibility] = useState<"public" | "private">("public");
  const [tagNames, setTagNames] = useState("");
  const [sessions, setSessions] = useState<SessionRow[]>([{ starts_at: "", duration_minutes: 60 }]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [createdEvent, setCreatedEvent] = useState<EventDetail | null>(null);
  const [bannerProgress, setBannerProgress] = useState<number | null>(null);
  const [videoProgress, setVideoProgress] = useState<number | null>(null);
  const [bannerFileName, setBannerFileName] = useState<string | null>(null);
  const [videoFileName, setVideoFileName] = useState<string | null>(null);
  const bannerInputRef = useRef<HTMLInputElement | null>(null);
  const videoInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    eventsApi.listCategories().then(setCategories).catch(() => setError("خطا در دریافت دسته‌بندی‌ها"));
  }, []);

  const categoryComboboxGroups = buildCategoryComboboxGroups(categories);
  const selectedCategoryItem =
    categoryComboboxGroups.flatMap((g) => g.items).find((i) => i.value === categoryId) ?? null;

  function updateSession(index: number, patch: Partial<SessionRow>) {
    setSessions((prev) => prev.map((s, i) => (i === index ? { ...s, ...patch } : s)));
  }

  function addSession() {
    setSessions((prev) => [...prev, { starts_at: "", duration_minutes: 60 }]);
  }

  function removeSession(index: number) {
    setSessions((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) {
      setError("برای ایجاد رویداد باید وارد شوید");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const sessionInputs: EventSessionInput[] = sessions
        .filter((s) => s.starts_at)
        .map((s) => ({
          starts_at: new Date(s.starts_at).toISOString(),
          duration_minutes: s.duration_minutes,
        }));

      const event = await eventsApi.create(
        {
          title,
          description,
          category_id: Number(categoryId),
          format,
          venue_address: format !== "online" ? venueAddress : undefined,
          online_platform_name: format !== "in_person" ? onlinePlatform : undefined,
          visibility,
          tag_names: tagNames
            .split(/[,#]/)
            .map((t) => t.trim())
            .filter(Boolean),
          sessions: sessionInputs,
        },
        accessToken,
      );
      setCreatedEvent(event);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ایجاد رویداد");
    } finally {
      setLoading(false);
    }
  }

  async function handleBannerUpload(file: File) {
    if (!accessToken || !createdEvent) return;
    setError(null);
    setBannerFileName(file.name);
    setBannerProgress(0);
    try {
      const updated = await eventsApi.uploadBanner(
        createdEvent.id,
        file,
        accessToken,
        setBannerProgress,
      );
      setCreatedEvent(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در آپلود بنر");
    } finally {
      setBannerProgress(null);
    }
  }

  async function handlePromoVideoUpload(file: File) {
    if (!accessToken || !createdEvent) return;
    setError(null);
    setVideoFileName(file.name);
    setVideoProgress(0);
    try {
      const updated = await eventsApi.uploadPromoVideo(
        createdEvent.id,
        file,
        accessToken,
        setVideoProgress,
      );
      setCreatedEvent(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در آپلود کلیپ");
    } finally {
      setVideoProgress(null);
    }
  }

  async function handlePublish() {
    if (!accessToken || !createdEvent) return;
    setError(null);
    try {
      const published = await eventsApi.publish(createdEvent.id, accessToken);
      router.push(`/events/${published.slug}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در انتشار رویداد");
    }
  }

  if (createdEvent) {
    return (
      <div className="mx-auto flex max-w-xl flex-col gap-6 px-4 py-10">
        <Card className="text-right">
          <CardHeader>
            <CardTitle>رویداد ایجاد شد 🎉</CardTitle>
            <CardDescription>
              اطلاعات پایه ذخیره شد، ولی رویداد هنوز برای عموم منتشر نشده. اختیاری
              می‌تونید همین‌جا یک بنر و یک کلیپ کوتاه تبلیغاتی برای معرفی بهتر رویداد
              اضافه کنید — یا این مرحله رو رد کنید و مستقیم دکمه‌ی «انتشار رویداد» پایین
              صفحه رو بزنید.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p>
              کد رویداد: <Badge variant="secondary">{createdEvent.event_code}</Badge>
            </p>
            <div className="flex flex-col gap-2">
              <Label htmlFor="banner">بنر رویداد (اختیاری)</Label>
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
                  انتخاب فایل بنر
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
              {createdEvent.banner_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={createdEvent.banner_url}
                  alt="بنر رویداد"
                  className="aspect-video w-full rounded-md object-cover"
                />
              )}
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="promo-video">کلیپ کوتاه تبلیغاتی (اختیاری، کنار بنر — حداکثر ۳۰ مگابایت، MP4/WebM)</Label>
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
                  انتخاب فایل کلیپ
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
              {createdEvent.promo_video_url && (
                <video
                  controls
                  preload="metadata"
                  src={createdEvent.promo_video_url}
                  className="aspect-video w-full rounded-md bg-black"
                />
              )}
            </div>
            <div className="rounded-md border border-dashed p-3 text-sm">
              <p className="mb-2">
                ⚠️ قبل از انتشار، حتماً حداقل یک <b>نوع بلیط</b> (حتی رایگان) اضافه کنید — بدون
                اون، خریداران هیچ گزینه‌ای برای ثبت‌نام نمی‌بینن.
              </p>
              <Link
                href={`/organizer/events/${createdEvent.id}/tickets`}
                className={buttonVariants({ variant: "outline", size: "sm" })}
              >
                مدیریت انواع بلیط
              </Link>
            </div>

            {error && <p className="text-destructive text-sm">{error}</p>}
            <Button onClick={handlePublish}>انتشار رویداد</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 px-4 py-10">
      <h1 className="text-2xl font-bold">ایجاد رویداد جدید</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5 text-right">
        <div className="flex flex-col gap-2">
          <Label htmlFor="title">عنوان رویداد</Label>
          <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="description">توضیحات</Label>
          <Textarea
            id="description"
            rows={5}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </div>

        <div className="flex flex-col gap-2">
          <Label>دسته‌بندی</Label>
          <Combobox
            items={categoryComboboxGroups}
            value={selectedCategoryItem}
            onValueChange={(item: CategoryComboboxItem | null) => setCategoryId(item ? item.value : "")}
            itemToStringLabel={(item: CategoryComboboxItem) => item.label}
            itemToStringValue={(item: CategoryComboboxItem) => item.value}
          >
            <ComboboxInputGroup>
              <ComboboxInput placeholder="جستجو یا انتخاب زیردسته..." />
              <ComboboxTrigger />
            </ComboboxInputGroup>
            <ComboboxContent>
              <ComboboxEmpty>موردی یافت نشد</ComboboxEmpty>
              <ComboboxList>
                {categoryComboboxGroups.map((group) => (
                  <ComboboxGroup key={group.label} items={group.items}>
                    <ComboboxGroupLabel>{group.label}</ComboboxGroupLabel>
                    <ComboboxCollection>
                      {(item: CategoryComboboxItem) => (
                        <ComboboxItem key={item.value} value={item}>
                          {item.label}
                        </ComboboxItem>
                      )}
                    </ComboboxCollection>
                  </ComboboxGroup>
                ))}
              </ComboboxList>
            </ComboboxContent>
          </Combobox>
        </div>

        <div className="flex flex-col gap-2">
          <Label>نوع برگزاری</Label>
          <Select value={format} onValueChange={(v) => v && setFormat(v as typeof format)}>
            <SelectTrigger className="w-full">
              <SelectValue>{(value: string) => FORMAT_LABELS[value] ?? value}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="online">آنلاین</SelectItem>
              <SelectItem value="in_person">حضوری</SelectItem>
              <SelectItem value="hybrid">ترکیبی</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {format !== "online" && (
          <div className="flex flex-col gap-2">
            <Label htmlFor="venue">آدرس محل برگزاری</Label>
            <Input
              id="venue"
              value={venueAddress}
              onChange={(e) => setVenueAddress(e.target.value)}
              required
            />
          </div>
        )}

        {format !== "in_person" && (
          <div className="flex flex-col gap-2">
            <Label htmlFor="platform">پلتفرم آنلاین (مثلاً SkyRoom)</Label>
            <Input
              id="platform"
              value={onlinePlatform}
              onChange={(e) => setOnlinePlatform(e.target.value)}
            />
          </div>
        )}

        <div className="flex flex-col gap-2">
          <Label>نوع دسترسی</Label>
          <Select value={visibility} onValueChange={(v) => v && setVisibility(v as typeof visibility)}>
            <SelectTrigger className="w-full">
              <SelectValue>{(value: string) => VISIBILITY_LABELS[value] ?? value}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="public">عمومی</SelectItem>
              <SelectItem value="private">خصوصی (فقط با لینک دعوت)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="tags">برچسب‌ها (با کاما یا # جدا کنید)</Label>
          <Input
            id="tags"
            dir="rtl"
            placeholder="هوش‌مصنوعی, کسب‌وکار"
            value={tagNames}
            onChange={(e) => setTagNames(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-3">
          <Label>جلسه‌ها</Label>
          {sessions.map((session, index) => (
            <div key={index} className="flex flex-wrap items-end gap-2 rounded-md border p-3">
              <div className="flex flex-col gap-1">
                <Label htmlFor={`session-start-${index}`}>تاریخ و ساعت شروع</Label>
                <JalaliDateTimePicker
                  id={`session-start-${index}`}
                  value={session.starts_at}
                  onChange={(isoString) => updateSession(index, { starts_at: isoString })}
                  required
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor={`session-duration-${index}`}>مدت (دقیقه)</Label>
                <Input
                  id={`session-duration-${index}`}
                  type="number"
                  min={1}
                  className="w-24"
                  value={session.duration_minutes}
                  onChange={(e) =>
                    updateSession(index, { duration_minutes: Number(e.target.value) })
                  }
                  required
                />
              </div>
              {sessions.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeSession(index)}
                >
                  حذف جلسه
                </Button>
              )}
            </div>
          ))}
          <Button type="button" variant="outline" size="sm" onClick={addSession}>
            + افزودن جلسه
          </Button>
        </div>

        {error && <p className="text-destructive text-sm">{error}</p>}

        <Button type="submit" disabled={loading || !categoryId}>
          ایجاد رویداد
        </Button>
      </form>
    </div>
  );
}
