"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { AdminEvent, AdminUser, AuditLogEntry } from "@/lib/admin-api";
import { adminApi } from "@/lib/admin-api";
import { ApiError } from "@/lib/api-client";
import type { CategoryOut } from "@/lib/events-api";
import { formatJalaliDateTime } from "@/lib/date";
import { useAuthStore } from "@/store/auth-store";

const EVENT_STATUS_LABELS: Record<AdminEvent["status"], string> = {
  draft: "پیش‌نویس",
  published: "منتشرشده",
  cancelled: "لغوشده",
};

const LAZY_CHUNK_SIZE = 10;

type Tab = "events" | "users" | "categories" | "audit";

export default function AdminPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const [tab, setTab] = useState<Tab>("events");

  const [events, setEvents] = useState<AdminEvent[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [categories, setCategories] = useState<CategoryOut[]>([]);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const [newCategoryName, setNewCategoryName] = useState("");
  const [newCategoryParentId, setNewCategoryParentId] = useState<string | null>(null);
  const [eventSearchQuery, setEventSearchQuery] = useState("");

  // نمایش تدریجی ۱۰تا ۱۰تا با اسکرول (به‌جای صفحه‌بندی دکمه‌ای)، یک state/ref/effect
  // جدا برای هر تب — یک ردیف sentinel وقتی وارد viewport بشه chunk بعدی رو نشون می‌ده.
  const [visibleEventsCount, setVisibleEventsCount] = useState(LAZY_CHUNK_SIZE);
  const eventsSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleUsersCount, setVisibleUsersCount] = useState(LAZY_CHUNK_SIZE);
  const usersSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleCategoriesCount, setVisibleCategoriesCount] = useState(LAZY_CHUNK_SIZE);
  const categoriesSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleAuditCount, setVisibleAuditCount] = useState(LAZY_CHUNK_SIZE);
  const auditSentinelRef = useRef<HTMLDivElement | null>(null);

  const trimmedEventSearch = eventSearchQuery.trim();
  const filteredEvents = trimmedEventSearch
    ? events.filter(
        (event) =>
          event.title.includes(trimmedEventSearch) ||
          event.event_code.includes(trimmedEventSearch) ||
          (event.organizer_name ?? "").includes(trimmedEventSearch),
      )
    : events;

  useEffect(() => {
    const sentinel = eventsSentinelRef.current;
    if (!sentinel || tab !== "events") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleEventsCount((prev) => prev + LAZY_CHUNK_SIZE);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [tab, filteredEvents.length, visibleEventsCount]);

  useEffect(() => {
    const sentinel = usersSentinelRef.current;
    if (!sentinel || tab !== "users") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleUsersCount((prev) => prev + LAZY_CHUNK_SIZE);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [tab, users.length, visibleUsersCount]);

  useEffect(() => {
    const sentinel = categoriesSentinelRef.current;
    if (!sentinel || tab !== "categories") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleCategoriesCount((prev) => prev + LAZY_CHUNK_SIZE);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [tab, categories.length, visibleCategoriesCount]);

  useEffect(() => {
    const sentinel = auditSentinelRef.current;
    if (!sentinel || tab !== "audit") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleAuditCount((prev) => prev + LAZY_CHUNK_SIZE);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [tab, auditLog.length, visibleAuditCount]);

  function loadAll(token: string) {
    Promise.all([
      adminApi.listEvents(token),
      adminApi.listUsers(token),
      adminApi.listCategories(token),
      adminApi.listAuditLog(token),
    ])
      .then(([e, u, c, a]) => {
        setEvents(e);
        setUsers(u);
        setCategories(c);
        setAuditLog(a);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "خطا در دریافت اطلاعات پنل ادمین"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!accessToken) return;
    loadAll(accessToken);
  }, [accessToken]);

  async function handleDeleteEvent(id: number) {
    if (!accessToken) return;
    if (!window.confirm("این رویداد و تمام سفارش/بلیط‌های مرتبط با آن برای همیشه حذف می‌شود. ادامه می‌دهید؟")) {
      return;
    }
    setBusyId(id);
    try {
      await adminApi.deleteEvent(id, accessToken);
      loadAll(accessToken);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در حذف رویداد");
    } finally {
      setBusyId(null);
    }
  }

  async function handleToggleFeatured(event: AdminEvent) {
    if (!accessToken) return;
    setBusyId(event.id);
    try {
      const updated = await adminApi.setEventFeatured(event.id, !event.is_featured, accessToken);
      setEvents((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در تغییر وضعیت ویژه");
    } finally {
      setBusyId(null);
    }
  }

  async function handleToggleSuspend(targetUser: AdminUser) {
    if (!accessToken) return;
    setBusyId(targetUser.id);
    try {
      const updated = await adminApi.setUserSuspended(
        targetUser.id,
        targetUser.status !== "suspended",
        accessToken,
      );
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در تغییر وضعیت کاربر");
    } finally {
      setBusyId(null);
    }
  }

  async function handleCreateCategory(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !newCategoryName.trim()) return;
    try {
      await adminApi.createCategory(
        newCategoryName.trim(),
        newCategoryParentId ? Number(newCategoryParentId) : null,
        accessToken,
      );
      setNewCategoryName("");
      setNewCategoryParentId(null);
      loadAll(accessToken);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ایجاد دسته‌بندی");
    }
  }

  async function handleDeleteCategory(id: number) {
    if (!accessToken) return;
    setBusyId(id);
    try {
      await adminApi.deleteCategory(id, accessToken);
      loadAll(accessToken);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در حذف دسته‌بندی");
    } finally {
      setBusyId(null);
    }
  }

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن پنل ادمین باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  if (user && user.role !== "admin") {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p className="text-destructive">این صفحه فقط برای ادمین قابل دسترسه.</p>
      </div>
    );
  }

  const parentCategories = categories.filter((c) => c.parent_id === null);
  const categoryParentName = (parentId: number | null) =>
    parentId ? categories.find((c) => c.id === parentId)?.name : null;

  const visibleEvents = filteredEvents.slice(0, visibleEventsCount);
  const hasMoreEvents = visibleEventsCount < filteredEvents.length;
  const visibleUsers = users.slice(0, visibleUsersCount);
  const hasMoreUsers = visibleUsersCount < users.length;
  const visibleCategories = categories.slice(0, visibleCategoriesCount);
  const hasMoreCategories = visibleCategoriesCount < categories.length;
  const visibleAuditLog = auditLog.slice(0, visibleAuditCount);
  const hasMoreAudit = visibleAuditCount < auditLog.length;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-10">
      <Breadcrumbs items={[{ label: "پنل ادمین" }]} />
      <h1 className="text-2xl font-bold">پنل ادمین</h1>

      {error && <p className="text-destructive text-sm">{error}</p>}
      {loading && <p className="text-muted-foreground">در حال بارگذاری...</p>}

      <Tabs value={tab} onValueChange={(v) => v && setTab(v as Tab)}>
        <TabsList>
          <TabsTrigger value="events">رویدادها</TabsTrigger>
          <TabsTrigger value="users">کاربران</TabsTrigger>
          <TabsTrigger value="categories">دسته‌بندی‌ها</TabsTrigger>
          <TabsTrigger value="audit">لاگ اقدامات</TabsTrigger>
        </TabsList>
      </Tabs>

      {tab === "events" && (
        <div className="flex flex-col gap-2">
          <Input
            type="search"
            placeholder="جستجو بر اساس عنوان، کد رویداد یا برگزارکننده..."
            value={eventSearchQuery}
            onChange={(e) => setEventSearchQuery(e.target.value)}
            className="max-w-sm"
          />
          {trimmedEventSearch && filteredEvents.length === 0 && (
            <p className="text-muted-foreground text-sm">موردی یافت نشد.</p>
          )}
          <div className="overflow-x-auto rounded-lg bg-[silver] ring-1 ring-foreground/10">
            <table className="w-full text-right text-sm">
              <thead className="bg-[#a8a8a8] text-xs text-zinc-700">
                <tr>
                  <th className="px-3 py-2 font-normal">ردیف</th>
                  <th className="px-3 py-2 font-normal">عنوان</th>
                  <th className="px-3 py-2 font-normal">وضعیت</th>
                  <th className="px-3 py-2 font-normal">برگزارکننده</th>
                  <th className="px-3 py-2 font-normal">کد</th>
                  <th className="px-3 py-2 font-normal">تاریخ ایجاد</th>
                  <th className="px-3 py-2 font-normal">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {visibleEvents.map((event, index) => (
                  <tr key={event.id} className="border-t border-zinc-400">
                    <td className="px-3 py-2 text-zinc-700">{index + 1}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-zinc-900">{event.title}</span>
                        {event.is_featured && <Badge className="text-[10px]">ویژه</Badge>}
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <Badge variant={event.status === "published" ? "default" : "secondary"}>
                        {EVENT_STATUS_LABELS[event.status]}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-zinc-700">
                      {event.organizer_name ?? "بدون نام"}
                    </td>
                    <td className="px-3 py-2 text-zinc-700">{event.event_code}</td>
                    <td className="px-3 py-2 text-zinc-700 whitespace-nowrap">
                      {formatJalaliDateTime(event.created_at)}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-nowrap gap-1.5">
                        <Link
                          href={`/organizer/events/${event.id}/edit`}
                          className={buttonVariants({
                            variant: "outline",
                            size: "sm",
                            className:
                              "whitespace-nowrap border border-cyan-600 bg-cyan-400 text-cyan-950 hover:bg-cyan-500",
                          })}
                        >
                          ویرایش
                        </Link>
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-[132px] shrink-0 whitespace-nowrap border border-cyan-600 bg-cyan-400 text-cyan-950 hover:bg-cyan-500"
                          disabled={busyId === event.id}
                          onClick={() => handleToggleFeatured(event)}
                        >
                          {event.is_featured ? "حذف از ویژه‌ها" : "افزودن به ویژه‌ها"}
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          className="whitespace-nowrap"
                          disabled={busyId === event.id}
                          onClick={() => handleDeleteEvent(event.id)}
                        >
                          حذف کامل
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
                {hasMoreEvents && (
                  <tr ref={eventsSentinelRef}>
                    <td colSpan={7} className="px-3 py-3 text-center text-xs text-zinc-600">
                      در حال بارگذاری موارد بیشتر...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "users" && (
        <div className="overflow-x-auto rounded-lg bg-[silver] ring-1 ring-foreground/10">
          <table className="w-full text-right text-sm">
            <thead className="bg-[#a8a8a8] text-xs text-zinc-700">
              <tr>
                <th className="px-3 py-2 font-normal">ردیف</th>
                <th className="px-3 py-2 font-normal">نام</th>
                <th className="px-3 py-2 font-normal">شماره/ایمیل</th>
                <th className="px-3 py-2 font-normal">نقش</th>
                <th className="px-3 py-2 font-normal">وضعیت</th>
                <th className="px-3 py-2 font-normal">عملیات</th>
              </tr>
            </thead>
            <tbody>
              {visibleUsers.map((u, index) => (
                <tr key={u.id} className="border-t border-zinc-400">
                  <td className="px-3 py-2 text-zinc-700">{index + 1}</td>
                  <td className="px-3 py-2 text-zinc-900">{u.full_name ?? "بدون نام"}</td>
                  <td className="px-3 py-2 text-zinc-700 whitespace-nowrap">
                    {u.phone ?? u.email ?? "بدون شماره/ایمیل"}
                  </td>
                  <td className="px-3 py-2 text-zinc-700">{u.role}</td>
                  <td className="px-3 py-2">
                    <Badge variant={u.status === "suspended" ? "destructive" : "secondary"}>
                      {u.status === "suspended" ? "تعلیق‌شده" : "فعال"}
                    </Badge>
                  </td>
                  <td className="px-3 py-2">
                    <Button
                      size="sm"
                      variant={u.status === "suspended" ? "outline" : "destructive"}
                      className="whitespace-nowrap"
                      disabled={busyId === u.id || u.role === "admin"}
                      onClick={() => handleToggleSuspend(u)}
                    >
                      {u.status === "suspended" ? "رفع تعلیق" : "تعلیق کاربر"}
                    </Button>
                  </td>
                </tr>
              ))}
              {hasMoreUsers && (
                <tr ref={usersSentinelRef}>
                  <td colSpan={6} className="px-3 py-3 text-center text-xs text-zinc-600">
                    در حال بارگذاری موارد بیشتر...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "categories" && (
        <div className="flex flex-col gap-6">
          <Card className="text-right">
            <CardHeader>
              <CardTitle className="text-base">افزودن دسته‌بندی</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateCategory} className="flex flex-wrap items-end gap-3">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="new-category-name">نام</Label>
                  <Input
                    id="new-category-name"
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label>دسته‌بندی</Label>
                  <Select
                    value={newCategoryParentId}
                    onValueChange={(v) => setNewCategoryParentId(v)}
                  >
                    <SelectTrigger className="w-48">
                      <SelectValue>
                        {(v) => parentCategories.find((c) => String(c.id) === v)?.name ?? "انتخاب"}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {parentCategories.map((c) => (
                        <SelectItem key={c.id} value={String(c.id)}>
                          {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button type="submit" disabled={!newCategoryName.trim()}>
                  افزودن
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="overflow-x-auto rounded-lg bg-[silver] ring-1 ring-foreground/10">
            <table className="w-full text-right text-sm">
              <thead className="bg-[#a8a8a8] text-xs text-zinc-700">
                <tr>
                  <th className="px-3 py-2 font-normal">ردیف</th>
                  <th className="px-3 py-2 font-normal">نام</th>
                  <th className="px-3 py-2 font-normal">دسته‌بندی</th>
                  <th className="px-3 py-2 font-normal">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {visibleCategories.map((c, index) => (
                  <tr key={c.id} className="border-t border-zinc-400">
                    <td className="px-3 py-2 text-zinc-700">{index + 1}</td>
                    <td className="px-3 py-2 text-zinc-900">{c.name}</td>
                    <td className="px-3 py-2 text-zinc-700">
                      {categoryParentName(c.parent_id) ?? "—"}
                    </td>
                    <td className="px-3 py-2">
                      <Button
                        size="sm"
                        variant="destructive"
                        className="whitespace-nowrap"
                        disabled={busyId === c.id}
                        onClick={() => handleDeleteCategory(c.id)}
                      >
                        حذف
                      </Button>
                    </td>
                  </tr>
                ))}
                {hasMoreCategories && (
                  <tr ref={categoriesSentinelRef}>
                    <td colSpan={4} className="px-3 py-3 text-center text-xs text-zinc-600">
                      در حال بارگذاری موارد بیشتر...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "audit" && (
        <div className="flex flex-col gap-2">
          {auditLog.length === 0 && <p className="text-muted-foreground">هنوز اقدامی ثبت نشده.</p>}
          {visibleAuditLog.map((entry) => (
            <Card key={entry.id} className="text-right">
              <CardContent className="flex flex-col gap-1 py-4 text-sm">
                <span>
                  <strong>{entry.admin_name ?? `ادمین #${entry.admin_user_id}`}</strong> — {entry.action} روی{" "}
                  {entry.target_type} #{entry.target_id}
                </span>
                {entry.reason && <span className="text-muted-foreground">دلیل: {entry.reason}</span>}
                <span className="text-muted-foreground text-xs">
                  {formatJalaliDateTime(entry.created_at)}
                </span>
              </CardContent>
            </Card>
          ))}
          {hasMoreAudit && (
            <div ref={auditSentinelRef} className="py-3 text-center text-xs text-muted-foreground">
              در حال بارگذاری موارد بیشتر...
            </div>
          )}
        </div>
      )}
    </div>
  );
}
