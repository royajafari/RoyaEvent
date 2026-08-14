"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

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

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-10">
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
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {events.map((event, index) => (
            <Card key={event.id} className="text-right">
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground text-xs">ردیف {index + 1}</span>
                  <CardTitle className="text-base">{event.title}</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  {event.is_featured && <Badge>ویژه</Badge>}
                  <Badge variant={event.status === "published" ? "default" : "secondary"}>
                    {EVENT_STATUS_LABELS[event.status]}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <span className="text-muted-foreground text-xs">
                  برگزارکننده: {event.organizer_name ?? "بدون نام"} — کد: {event.event_code}
                </span>
                <span className="text-muted-foreground text-xs">
                  تاریخ ایجاد: {formatJalaliDateTime(event.created_at)}
                </span>
                <div className="flex flex-wrap gap-2">
                  <Link
                    href={`/organizer/events/${event.id}/edit`}
                    className={buttonVariants({ variant: "outline", size: "sm" })}
                  >
                    ویرایش
                  </Link>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busyId === event.id}
                    onClick={() => handleToggleFeatured(event)}
                  >
                    {event.is_featured ? "حذف از ویژه‌ها" : "افزودن به ویژه‌ها"}
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    disabled={busyId === event.id}
                    onClick={() => handleDeleteEvent(event.id)}
                  >
                    حذف کامل
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {tab === "users" && (
        <div className="flex flex-col gap-3">
          {users.map((u) => (
            <Card key={u.id} className="text-right">
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">{u.full_name ?? "بدون نام"}</CardTitle>
                <Badge variant={u.status === "suspended" ? "destructive" : "secondary"}>
                  {u.status === "suspended" ? "تعلیق‌شده" : "فعال"}
                </Badge>
              </CardHeader>
              <CardContent className="flex flex-wrap items-center gap-2">
                <span className="text-muted-foreground text-xs">
                  {u.phone ?? u.email ?? "بدون شماره/ایمیل"} — نقش: {u.role}
                </span>
                <Button
                  size="sm"
                  variant={u.status === "suspended" ? "outline" : "destructive"}
                  className="mr-auto"
                  disabled={busyId === u.id || u.role === "admin"}
                  onClick={() => handleToggleSuspend(u)}
                >
                  {u.status === "suspended" ? "رفع تعلیق" : "تعلیق کاربر"}
                </Button>
              </CardContent>
            </Card>
          ))}
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
                  <Label>دسته‌ی والد (اختیاری)</Label>
                  <Select
                    value={newCategoryParentId}
                    onValueChange={(v) => setNewCategoryParentId(v)}
                  >
                    <SelectTrigger className="w-48">
                      <SelectValue>
                        {(v) => parentCategories.find((c) => String(c.id) === v)?.name ?? "بدون والد"}
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

          <div className="flex flex-col gap-2">
            {categories.map((c) => (
              <Card key={c.id} className="text-right">
                <CardContent className="flex items-center justify-between py-4">
                  <span>
                    {c.name}
                    {categoryParentName(c.parent_id) && (
                      <span className="text-muted-foreground text-xs">
                        {" "}
                        (زیردسته‌ی {categoryParentName(c.parent_id)})
                      </span>
                    )}
                  </span>
                  <Button
                    size="sm"
                    variant="destructive"
                    disabled={busyId === c.id}
                    onClick={() => handleDeleteCategory(c.id)}
                  >
                    حذف
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {tab === "audit" && (
        <div className="flex flex-col gap-2">
          {auditLog.length === 0 && <p className="text-muted-foreground">هنوز اقدامی ثبت نشده.</p>}
          {auditLog.map((entry) => (
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
        </div>
      )}
    </div>
  );
}
