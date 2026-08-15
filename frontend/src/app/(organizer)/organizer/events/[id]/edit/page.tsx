"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { JalaliDateTimePicker } from "@/components/JalaliDateTimePicker";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client";
import type { CategoryOut, EventDetail, EventSessionInput } from "@/lib/events-api";
import { eventsApi } from "@/lib/events-api";
import { useAuthStore } from "@/store/auth-store";

type SessionRow = { starts_at: string; duration_minutes: number; online_join_url: string };

const FORMAT_LABELS: Record<string, string> = {
  online: "آنلاین",
  in_person: "حضوری",
  hybrid: "ترکیبی",
};

type CategoryComboboxItem = { value: string; label: string };

function buildCategoryComboboxGroups(categories: CategoryOut[]) {
  const parents = categories.filter((c) => c.parent_id === null);
  return parents.map((parent) => ({
    label: parent.name,
    items: categories
      .filter((c) => c.parent_id === parent.id)
      .map((child): CategoryComboboxItem => ({ value: String(child.id), label: child.name })),
  }));
}

export default function EditEventPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const eventId = Number(id);
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);

  const [categories, setCategories] = useState<CategoryOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [format, setFormat] = useState<"online" | "in_person" | "hybrid">("online");
  const [venueAddress, setVenueAddress] = useState("");
  const [onlinePlatform, setOnlinePlatform] = useState("");
  const [refundPolicy, setRefundPolicy] = useState("");
  const [tagNames, setTagNames] = useState("");
  const [instructorNames, setInstructorNames] = useState("");
  const [isInstantRegistration, setIsInstantRegistration] = useState(false);
  const [sessions, setSessions] = useState<SessionRow[]>([{ starts_at: "", duration_minutes: 60, online_join_url: "" }]);

  useEffect(() => {
    if (!accessToken) return;
    Promise.all([eventsApi.getById(eventId, accessToken), eventsApi.listCategories()])
      .then(([event, cats]: [EventDetail, CategoryOut[]]) => {
        setCategories(cats);
        setTitle(event.title);
        setDescription(event.description);
        setCategoryId(event.category ? String(event.category.id) : "");
        setFormat(event.format);
        setVenueAddress(event.venue_address ?? "");
        setOnlinePlatform(event.online_platform_name ?? "");
        setRefundPolicy(event.refund_policy ?? "");
        setTagNames(event.tags.map((t) => t.name).join(", "));
        setInstructorNames(event.instructors.map((i) => i.name).join(", "));
        setIsInstantRegistration(event.is_instant_registration);
        setSessions(
          event.sessions.map((s) => ({
            starts_at: s.starts_at,
            duration_minutes: s.duration_minutes,
            online_join_url: s.online_join_url ?? "",
          })),
        );
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت رویداد"))
      .finally(() => setLoading(false));
  }, [accessToken, eventId]);

  const categoryComboboxGroups = buildCategoryComboboxGroups(categories);
  const selectedCategoryItem =
    categoryComboboxGroups.flatMap((g) => g.items).find((i) => i.value === categoryId) ?? null;

  function updateSession(index: number, patch: Partial<SessionRow>) {
    setSessions((prev) => prev.map((s, i) => (i === index ? { ...s, ...patch } : s)));
  }

  function addSession() {
    setSessions((prev) => [...prev, { starts_at: "", duration_minutes: 60, online_join_url: "" }]);
  }

  function removeSession(index: number) {
    setSessions((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    setError(null);
    setSaved(false);
    setSaving(true);
    try {
      await eventsApi.update(
        eventId,
        {
          title,
          description,
          category_id: Number(categoryId),
          format,
          venue_address: format !== "online" ? venueAddress : undefined,
          online_platform_name: format !== "in_person" ? onlinePlatform : undefined,
          refund_policy: refundPolicy || undefined,
          tag_names: tagNames
            .split(/[,#]/)
            .map((t) => t.trim())
            .filter(Boolean),
          instructor_names: instructorNames
            .split(",")
            .map((t) => t.trim())
            .filter(Boolean),
          is_instant_registration: isInstantRegistration,
        },
        accessToken,
      );

      const sessionInputs: EventSessionInput[] = sessions
        .filter((s) => s.starts_at)
        .map((s) => ({
          starts_at: new Date(s.starts_at).toISOString(),
          duration_minutes: s.duration_minutes,
          online_join_url: format !== "in_person" && s.online_join_url ? s.online_join_url : undefined,
        }));
      await eventsApi.replaceSessions(eventId, sessionInputs, accessToken);

      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ذخیره‌ی تغییرات");
    } finally {
      setSaving(false);
    }
  }

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای ویرایش رویداد باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 px-4 py-10">
      <h1 className="text-2xl font-bold">ویرایش رویداد</h1>

      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}

      {!loading && (
        <Card className="text-right">
          <CardHeader>
            <CardTitle className="text-base">اطلاعات رویداد</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
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
                  onValueChange={(item: CategoryComboboxItem | null) =>
                    setCategoryId(item ? item.value : "")
                  }
                  itemToStringLabel={(item: CategoryComboboxItem) => item.label}
                  itemToStringValue={(item: CategoryComboboxItem) => item.value}
                >
                  <ComboboxInputGroup required>
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
                  <SelectTrigger required className="w-full">
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
                    required
                  />
                </div>
              )}

              <div className="flex flex-col gap-2">
                <Label htmlFor="refund-policy">قوانین بازگشت وجه (اختیاری)</Label>
                <Textarea
                  id="refund-policy"
                  rows={3}
                  value={refundPolicy}
                  onChange={(e) => setRefundPolicy(e.target.value)}
                />
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="tags">برچسب‌ها (با کاما یا # جدا کنید)</Label>
                <Input
                  id="tags"
                  dir="rtl"
                  value={tagNames}
                  onChange={(e) => setTagNames(e.target.value)}
                />
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="instructors">مدرس‌ها (با کاما جدا کنید، اختیاری)</Label>
                <Input
                  id="instructors"
                  dir="rtl"
                  value={instructorNames}
                  onChange={(e) => setInstructorNames(e.target.value)}
                />
              </div>

              <div className="flex items-start gap-2">
                <Checkbox
                  id="instant-registration"
                  checked={isInstantRegistration}
                  onCheckedChange={(checked) => setIsInstantRegistration(checked === true)}
                />
                <Label htmlFor="instant-registration">ثبت‌نام فوری</Label>
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
                    {format !== "in_person" && (
                      <div className="flex min-w-48 flex-1 flex-col gap-1">
                        <Label htmlFor={`session-join-url-${index}`}>لینک ورود آنلاین</Label>
                        <Input
                          id={`session-join-url-${index}`}
                          dir="ltr"
                          type="url"
                          placeholder="https://..."
                          value={session.online_join_url}
                          onChange={(e) =>
                            updateSession(index, { online_join_url: e.target.value })
                          }
                        />
                      </div>
                    )}
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
              {saved && !error && (
                <p className="text-sm text-green-600 dark:text-green-500">تغییرات ذخیره شد ✓</p>
              )}

              <div className="flex items-center gap-2">
                <Button type="submit" disabled={saving || !title.trim() || !categoryId}>
                  {saving ? "در حال ذخیره..." : "ذخیره‌ی تغییرات"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push("/events/mine")}
                >
                  بازگشت
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
