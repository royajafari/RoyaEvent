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
import type {
  AdminEvent,
  AdminNotification,
  AdminReview,
  AdminUser,
  AuditLogEntry,
  KpiSnapshot,
} from "@/lib/admin-api";
import { adminApi } from "@/lib/admin-api";
import { ApiError } from "@/lib/api-client";
import type { CategoryOut } from "@/lib/events-api";
import { formatJalaliDate, formatJalaliDateTime } from "@/lib/date";
import { useAuthStore } from "@/store/auth-store";

const EVENT_STATUS_LABELS: Record<AdminEvent["status"], string> = {
  draft: "پیش‌نویس",
  published: "منتشرشده",
  cancelled: "لغوشده",
};

const NOTIFICATION_CHANNEL_LABELS: Record<AdminNotification["channel"], string> = {
  sms: "پیامک",
  email: "ایمیل",
};

const NOTIFICATION_STATUS_LABELS: Record<AdminNotification["status"], string> = {
  pending: "در انتظار ارسال",
  sent: "ارسال‌شده",
  failed: "ناموفق",
};

const NOTIFICATION_TEMPLATE_LABELS: Record<string, string> = {
  registration_complete: "تأیید ثبت‌نام",
  ticket_purchase_complete: "تأیید خرید بلیط",
  event_reminder_1h: "یادآوری ۱ساعته",
};

const REVIEW_STATUS_LABELS: Record<AdminReview["status"], string> = {
  published: "منتشرشده",
  hidden: "مخفی",
};

const KPI_METRIC_LABELS: Record<string, string> = {
  funnel_view_event: "قیف — بازدید رویداد",
  funnel_click_register: "قیف — کلیک ثبت‌نام",
  funnel_start_checkout: "قیف — شروع تسویه‌حساب",
  funnel_complete_order: "قیف — تکمیل سفارش",
  funnel_conversion_view_to_complete_pct: "نرخ تبدیل بازدید به سفارش (٪)",
  search_total_queries: "تعداد کل جستجوها",
  search_failed_queries: "جستجوهای بی‌نتیجه",
  search_keyword: "کلیدواژه‌ی پرجستجو",
  dau: "کاربران فعال روزانه (DAU)",
  otp_requested: "درخواست کد OTP",
  otp_verified: "تأیید موفق OTP",
};

const LAZY_CHUNK_SIZE = 10;
// بازه‌ی گسترده‌تر از بقیه‌ی تب‌ها چون نمای ماهانه‌ی KPI به چند ماه داده نیاز داره.
const KPI_FETCH_DAYS = 180;

function jalaliMonthOf(dateStr: string): { sortKey: string; label: string } {
  const date = new Date(dateStr);
  const numericParts = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    year: "numeric",
    month: "2-digit",
  }).formatToParts(date);
  const year = numericParts.find((p) => p.type === "year")?.value ?? "";
  const month = numericParts.find((p) => p.type === "month")?.value ?? "";
  const label = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    year: "numeric",
    month: "long",
  }).format(date);
  return { sortKey: `${year}-${month}`, label };
}

// جمع ساده‌ی مقدارها به تفکیک ماه شمسی + معیار + جزئیات — به‌جز نرخ تبدیل
// قیف که جمع/میانگین درصدهای روزانه‌اش ریاضی‌اش غلطه؛ اون یکی از مجموع
// بازدید/تکمیل سفارش همون ماه دوباره محاسبه می‌شه.
function aggregateMonthlyKpis(rows: KpiSnapshot[]): KpiSnapshot[] {
  const sums = new Map<string, KpiSnapshot & { sortKey: string }>();
  for (const row of rows) {
    const { sortKey, label } = jalaliMonthOf(row.date);
    const groupKey = `${sortKey}__${row.metric_name}__${JSON.stringify(row.dimensions)}`;
    const existing = sums.get(groupKey);
    if (existing) {
      existing.value += row.value;
    } else {
      sums.set(groupKey, { ...row, date: label, sortKey, value: row.value });
    }
  }

  const monthlyFunnelCounts = new Map<string, { view: number; complete: number }>();
  for (const row of rows) {
    const { sortKey } = jalaliMonthOf(row.date);
    const bucket = monthlyFunnelCounts.get(sortKey) ?? { view: 0, complete: 0 };
    if (row.metric_name === "funnel_view_event") bucket.view += row.value;
    if (row.metric_name === "funnel_complete_order") bucket.complete += row.value;
    monthlyFunnelCounts.set(sortKey, bucket);
  }
  for (const entry of sums.values()) {
    if (entry.metric_name === "funnel_conversion_view_to_complete_pct") {
      const counts = monthlyFunnelCounts.get(entry.sortKey);
      entry.value = counts && counts.view > 0 ? (counts.complete / counts.view) * 100 : 0;
    }
  }

  return Array.from(sums.values()).sort((a, b) => b.sortKey.localeCompare(a.sortKey));
}

type Tab = "events" | "users" | "categories" | "audit" | "notifications" | "reviews" | "kpis";

export default function AdminPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const [tab, setTab] = useState<Tab>("events");

  const [events, setEvents] = useState<AdminEvent[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [categories, setCategories] = useState<CategoryOut[]>([]);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [notifications, setNotifications] = useState<AdminNotification[]>([]);
  const [reviews, setReviews] = useState<AdminReview[]>([]);
  const [kpis, setKpis] = useState<KpiSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [rollingUp, setRollingUp] = useState(false);

  const [newCategoryName, setNewCategoryName] = useState("");
  const [newCategoryParentId, setNewCategoryParentId] = useState<string | null>(null);
  const [eventSearchQuery, setEventSearchQuery] = useState("");
  const [userSearchQuery, setUserSearchQuery] = useState("");
  const [categorySearchQuery, setCategorySearchQuery] = useState("");
  const [auditSearchQuery, setAuditSearchQuery] = useState("");
  const [notificationSearchQuery, setNotificationSearchQuery] = useState("");
  const [reviewSearchQuery, setReviewSearchQuery] = useState("");
  const [kpiSearchQuery, setKpiSearchQuery] = useState("");
  const [kpiGranularity, setKpiGranularity] = useState<"daily" | "monthly">("daily");

  const categoryParentName = (parentId: number | null) =>
    parentId ? categories.find((c) => c.id === parentId)?.name : null;

  const auditTargetLabel = (entry: AuditLogEntry): string => {
    if (entry.target_type === "event") {
      return events.find((e) => e.id === entry.target_id)?.title ?? `رویداد #${entry.target_id}`;
    }
    if (entry.target_type === "user") {
      const target = users.find((u) => u.id === entry.target_id);
      return target ? (target.full_name ?? target.phone ?? target.email ?? `کاربر #${entry.target_id}`) : `کاربر #${entry.target_id}`;
    }
    if (entry.target_type === "category") {
      return categories.find((c) => c.id === entry.target_id)?.name ?? `دسته‌بندی #${entry.target_id}`;
    }
    return `${entry.target_type} #${entry.target_id}`;
  };

  // نمایش تدریجی ۱۰تا ۱۰تا با اسکرول (به‌جای صفحه‌بندی دکمه‌ای)، یک state/ref/effect
  // جدا برای هر تب — یک ردیف sentinel وقتی وارد viewport بشه chunk بعدی رو نشون می‌ده.
  const [visibleEventsCount, setVisibleEventsCount] = useState(LAZY_CHUNK_SIZE);
  const eventsSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleUsersCount, setVisibleUsersCount] = useState(LAZY_CHUNK_SIZE);
  const usersSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleCategoriesCount, setVisibleCategoriesCount] = useState(LAZY_CHUNK_SIZE);
  const categoriesSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleAuditCount, setVisibleAuditCount] = useState(LAZY_CHUNK_SIZE);
  const auditSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleNotificationsCount, setVisibleNotificationsCount] = useState(LAZY_CHUNK_SIZE);
  const notificationsSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleReviewsCount, setVisibleReviewsCount] = useState(LAZY_CHUNK_SIZE);
  const reviewsSentinelRef = useRef<HTMLTableRowElement | null>(null);
  const [visibleKpisCount, setVisibleKpisCount] = useState(LAZY_CHUNK_SIZE);
  const kpisSentinelRef = useRef<HTMLTableRowElement | null>(null);

  const trimmedEventSearch = eventSearchQuery.trim();
  const filteredEvents = trimmedEventSearch
    ? events.filter(
        (event) =>
          event.title.includes(trimmedEventSearch) ||
          event.event_code.includes(trimmedEventSearch) ||
          (event.organizer_name ?? "").includes(trimmedEventSearch),
      )
    : events;

  const trimmedUserSearch = userSearchQuery.trim();
  const filteredUsers = trimmedUserSearch
    ? users.filter(
        (u) =>
          (u.full_name ?? "").includes(trimmedUserSearch) ||
          (u.phone ?? "").includes(trimmedUserSearch) ||
          (u.email ?? "").includes(trimmedUserSearch) ||
          u.role.includes(trimmedUserSearch),
      )
    : users;

  const trimmedCategorySearch = categorySearchQuery.trim();
  const filteredCategories = trimmedCategorySearch
    ? categories.filter(
        (c) =>
          c.name.includes(trimmedCategorySearch) ||
          (categoryParentName(c.parent_id) ?? "").includes(trimmedCategorySearch),
      )
    : categories;

  const trimmedAuditSearch = auditSearchQuery.trim();
  const filteredAuditLog = trimmedAuditSearch
    ? auditLog.filter(
        (entry) =>
          (entry.admin_name ?? "").includes(trimmedAuditSearch) ||
          entry.action.includes(trimmedAuditSearch) ||
          auditTargetLabel(entry).includes(trimmedAuditSearch) ||
          (entry.reason ?? "").includes(trimmedAuditSearch),
      )
    : auditLog;

  const trimmedNotificationSearch = notificationSearchQuery.trim();
  const filteredNotifications = trimmedNotificationSearch
    ? notifications.filter(
        (n) =>
          n.destination.includes(trimmedNotificationSearch) ||
          (n.event_title ?? "").includes(trimmedNotificationSearch) ||
          (NOTIFICATION_TEMPLATE_LABELS[n.template_key] ?? n.template_key).includes(
            trimmedNotificationSearch,
          ),
      )
    : notifications;

  const trimmedReviewSearch = reviewSearchQuery.trim();
  const filteredReviews = trimmedReviewSearch
    ? reviews.filter(
        (r) =>
          r.event_title.includes(trimmedReviewSearch) ||
          (r.user_name ?? "").includes(trimmedReviewSearch) ||
          (r.comment_text ?? "").includes(trimmedReviewSearch),
      )
    : reviews;

  const granularKpis = kpiGranularity === "monthly" ? aggregateMonthlyKpis(kpis) : kpis;
  const trimmedKpiSearch = kpiSearchQuery.trim();
  const filteredKpis = trimmedKpiSearch
    ? granularKpis.filter(
        (k) =>
          (KPI_METRIC_LABELS[k.metric_name] ?? k.metric_name).includes(trimmedKpiSearch) ||
          k.date.includes(trimmedKpiSearch) ||
          Object.values(k.dimensions).some((v) => v.includes(trimmedKpiSearch)),
      )
    : granularKpis;

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
  }, [tab, filteredUsers.length, visibleUsersCount]);

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
  }, [tab, filteredCategories.length, visibleCategoriesCount]);

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
  }, [tab, filteredAuditLog.length, visibleAuditCount]);

  useEffect(() => {
    const sentinel = notificationsSentinelRef.current;
    if (!sentinel || tab !== "notifications") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleNotificationsCount((prev) => prev + LAZY_CHUNK_SIZE);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [tab, filteredNotifications.length, visibleNotificationsCount]);

  useEffect(() => {
    const sentinel = reviewsSentinelRef.current;
    if (!sentinel || tab !== "reviews") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleReviewsCount((prev) => prev + LAZY_CHUNK_SIZE);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [tab, filteredReviews.length, visibleReviewsCount]);

  useEffect(() => {
    const sentinel = kpisSentinelRef.current;
    if (!sentinel || tab !== "kpis") return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleKpisCount((prev) => prev + LAZY_CHUNK_SIZE);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [tab, filteredKpis.length, visibleKpisCount]);

  function loadAll(token: string) {
    Promise.all([
      adminApi.listEvents(token),
      adminApi.listUsers(token),
      adminApi.listCategories(token),
      adminApi.listAuditLog(token),
      adminApi.listNotifications(token),
      adminApi.listReviews(token),
      adminApi.getKpiReport(KPI_FETCH_DAYS, token),
    ])
      .then(([e, u, c, a, n, r, k]) => {
        setEvents(e);
        setUsers(u);
        setCategories(c);
        setAuditLog(a);
        setNotifications(n);
        setReviews(r);
        setKpis(k);
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

  async function handleToggleReviewHidden(review: AdminReview) {
    if (!accessToken) return;
    const hidden = review.status !== "hidden";
    let reason: string | undefined;
    if (hidden) {
      const promptResult = window.prompt("دلیل مخفی‌کردن نظر (اختیاری):");
      if (promptResult === null) return; // انصراف از پرامپت = انصراف از کل اقدام
      reason = promptResult || undefined;
    }
    setBusyId(review.id);
    try {
      const updated = await adminApi.setReviewHidden(review.id, hidden, accessToken, reason);
      setReviews((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در تغییر وضعیت نظر");
    } finally {
      setBusyId(null);
    }
  }

  async function handleRollupYesterday() {
    if (!accessToken) return;
    setRollingUp(true);
    setError(null);
    try {
      await adminApi.rollupKpis(null, accessToken);
      loadAll(accessToken);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در محاسبه‌ی KPI");
    } finally {
      setRollingUp(false);
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

  const visibleEvents = filteredEvents.slice(0, visibleEventsCount);
  const hasMoreEvents = visibleEventsCount < filteredEvents.length;
  const visibleUsers = filteredUsers.slice(0, visibleUsersCount);
  const hasMoreUsers = visibleUsersCount < filteredUsers.length;
  const visibleCategories = filteredCategories.slice(0, visibleCategoriesCount);
  const hasMoreCategories = visibleCategoriesCount < filteredCategories.length;
  const visibleAuditLog = filteredAuditLog.slice(0, visibleAuditCount);
  const hasMoreAudit = visibleAuditCount < filteredAuditLog.length;
  const visibleNotifications = filteredNotifications.slice(0, visibleNotificationsCount);
  const hasMoreNotifications = visibleNotificationsCount < filteredNotifications.length;
  const visibleReviews = filteredReviews.slice(0, visibleReviewsCount);
  const hasMoreReviews = visibleReviewsCount < filteredReviews.length;
  const visibleKpis = filteredKpis.slice(0, visibleKpisCount);
  const hasMoreKpis = visibleKpisCount < filteredKpis.length;

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
          <TabsTrigger value="notifications">پیامک‌ها و ایمیل‌ها</TabsTrigger>
          <TabsTrigger value="reviews">نظرات</TabsTrigger>
          <TabsTrigger value="kpis">آمار و KPI</TabsTrigger>
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
        <div className="flex flex-col gap-2">
          <Input
            type="search"
            placeholder="جستجو بر اساس نام، شماره، ایمیل یا نقش..."
            value={userSearchQuery}
            onChange={(e) => setUserSearchQuery(e.target.value)}
            className="max-w-sm"
          />
          {trimmedUserSearch && filteredUsers.length === 0 && (
            <p className="text-muted-foreground text-sm">موردی یافت نشد.</p>
          )}
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

          <Input
            type="search"
            placeholder="جستجو بر اساس نام دسته‌بندی..."
            value={categorySearchQuery}
            onChange={(e) => setCategorySearchQuery(e.target.value)}
            className="max-w-sm"
          />
          {trimmedCategorySearch && filteredCategories.length === 0 && (
            <p className="text-muted-foreground text-sm">موردی یافت نشد.</p>
          )}
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
          {auditLog.length > 0 && (
            <Input
              type="search"
              placeholder="جستجو بر اساس ادمین، اقدام، هدف یا دلیل..."
              value={auditSearchQuery}
              onChange={(e) => setAuditSearchQuery(e.target.value)}
              className="max-w-sm"
            />
          )}
          {trimmedAuditSearch && filteredAuditLog.length === 0 && (
            <p className="text-muted-foreground text-sm">موردی یافت نشد.</p>
          )}
          {filteredAuditLog.length > 0 && (
            <div className="overflow-x-auto rounded-lg bg-[silver] ring-1 ring-foreground/10">
              <table className="w-full text-right text-sm">
                <thead className="bg-[#a8a8a8] text-xs text-zinc-700">
                  <tr>
                    <th className="px-3 py-2 font-normal">ردیف</th>
                    <th className="px-3 py-2 font-normal">ادمین</th>
                    <th className="px-3 py-2 font-normal">اقدام</th>
                    <th className="px-3 py-2 font-normal">هدف</th>
                    <th className="px-3 py-2 font-normal">دلیل</th>
                    <th className="px-3 py-2 font-normal">تاریخ</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleAuditLog.map((entry, index) => (
                    <tr key={entry.id} className="border-t border-zinc-400">
                      <td className="px-3 py-2 text-zinc-700">{index + 1}</td>
                      <td className="px-3 py-2 text-zinc-900">
                        {entry.admin_name ?? `ادمین #${entry.admin_user_id}`}
                      </td>
                      <td className="px-3 py-2 text-zinc-700">{entry.action}</td>
                      <td className="px-3 py-2 text-zinc-700">{auditTargetLabel(entry)}</td>
                      <td className="px-3 py-2 text-zinc-700">{entry.reason ?? "—"}</td>
                      <td className="px-3 py-2 text-zinc-700 whitespace-nowrap">
                        {formatJalaliDateTime(entry.created_at)}
                      </td>
                    </tr>
                  ))}
                  {hasMoreAudit && (
                    <tr ref={auditSentinelRef}>
                      <td colSpan={6} className="px-3 py-3 text-center text-xs text-zinc-600">
                        در حال بارگذاری موارد بیشتر...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "notifications" && (
        <div className="flex flex-col gap-2">
          {notifications.length === 0 && (
            <p className="text-muted-foreground">هنوز پیامک/ایمیلی در صف نبوده.</p>
          )}
          {notifications.length > 0 && (
            <Input
              type="search"
              placeholder="جستجو بر اساس مقصد، رویداد یا قالب..."
              value={notificationSearchQuery}
              onChange={(e) => setNotificationSearchQuery(e.target.value)}
              className="max-w-sm"
            />
          )}
          {trimmedNotificationSearch && filteredNotifications.length === 0 && (
            <p className="text-muted-foreground text-sm">موردی یافت نشد.</p>
          )}
          {filteredNotifications.length > 0 && (
            <div className="overflow-x-auto rounded-lg bg-[silver] ring-1 ring-foreground/10">
              <table className="w-full text-right text-sm">
                <thead className="bg-[#a8a8a8] text-xs text-zinc-700">
                  <tr>
                    <th className="px-3 py-2 font-normal">ردیف</th>
                    <th className="px-3 py-2 font-normal">کانال</th>
                    <th className="px-3 py-2 font-normal">مقصد</th>
                    <th className="px-3 py-2 font-normal">قالب</th>
                    <th className="px-3 py-2 font-normal">رویداد</th>
                    <th className="px-3 py-2 font-normal">وضعیت</th>
                    <th className="px-3 py-2 font-normal">تلاش‌ها</th>
                    <th className="px-3 py-2 font-normal">تاریخ</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleNotifications.map((n, index) => (
                    <tr key={n.id} className="border-t border-zinc-400">
                      <td className="px-3 py-2 text-zinc-700">{index + 1}</td>
                      <td className="px-3 py-2 text-zinc-900">
                        {NOTIFICATION_CHANNEL_LABELS[n.channel]}
                      </td>
                      <td className="px-3 py-2 text-zinc-700 whitespace-nowrap" dir="ltr">
                        {n.destination}
                      </td>
                      <td className="px-3 py-2 text-zinc-700">
                        {NOTIFICATION_TEMPLATE_LABELS[n.template_key] ?? n.template_key}
                      </td>
                      <td className="px-3 py-2 text-zinc-700">{n.event_title ?? "—"}</td>
                      <td className="px-3 py-2">
                        <Badge
                          variant={
                            n.status === "sent"
                              ? "default"
                              : n.status === "failed"
                                ? "destructive"
                                : "secondary"
                          }
                        >
                          {NOTIFICATION_STATUS_LABELS[n.status]}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-zinc-700">{n.attempts}</td>
                      <td className="px-3 py-2 text-zinc-700 whitespace-nowrap">
                        {formatJalaliDateTime(n.created_at)}
                      </td>
                    </tr>
                  ))}
                  {hasMoreNotifications && (
                    <tr ref={notificationsSentinelRef}>
                      <td colSpan={8} className="px-3 py-3 text-center text-xs text-zinc-600">
                        در حال بارگذاری موارد بیشتر...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "reviews" && (
        <div className="flex flex-col gap-2">
          {reviews.length === 0 && <p className="text-muted-foreground">هنوز نظری ثبت نشده.</p>}
          {reviews.length > 0 && (
            <Input
              type="search"
              placeholder="جستجو بر اساس رویداد، کاربر یا متن نظر..."
              value={reviewSearchQuery}
              onChange={(e) => setReviewSearchQuery(e.target.value)}
              className="max-w-sm"
            />
          )}
          {trimmedReviewSearch && filteredReviews.length === 0 && (
            <p className="text-muted-foreground text-sm">موردی یافت نشد.</p>
          )}
          {filteredReviews.length > 0 && (
            <div className="overflow-x-auto rounded-lg bg-[silver] ring-1 ring-foreground/10">
              <table className="w-full text-right text-sm">
                <thead className="bg-[#a8a8a8] text-xs text-zinc-700">
                  <tr>
                    <th className="px-3 py-2 font-normal">ردیف</th>
                    <th className="px-3 py-2 font-normal">رویداد</th>
                    <th className="px-3 py-2 font-normal">کاربر</th>
                    <th className="px-3 py-2 font-normal">امتیاز</th>
                    <th className="px-3 py-2 font-normal">نظر</th>
                    <th className="px-3 py-2 font-normal">وضعیت</th>
                    <th className="px-3 py-2 font-normal">تاریخ</th>
                    <th className="px-3 py-2 font-normal">عملیات</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleReviews.map((r, index) => (
                    <tr key={r.id} className="border-t border-zinc-400">
                      <td className="px-3 py-2 text-zinc-700">{index + 1}</td>
                      <td className="px-3 py-2 text-zinc-900">{r.event_title}</td>
                      <td className="px-3 py-2 text-zinc-700">{r.user_name ?? `کاربر #${r.user_id}`}</td>
                      <td className="px-3 py-2 text-zinc-700" dir="ltr">
                        {r.overall_computed.toFixed(1)} / ۵
                      </td>
                      <td className="max-w-xs px-3 py-2 text-zinc-700">
                        <span className="line-clamp-2">{r.comment_text ?? "—"}</span>
                        {r.hidden_reason && (
                          <span className="text-muted-foreground block text-xs">
                            دلیل مخفی‌کردن: {r.hidden_reason}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant={r.status === "hidden" ? "secondary" : "default"}>
                          {REVIEW_STATUS_LABELS[r.status]}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-zinc-700 whitespace-nowrap">
                        {formatJalaliDateTime(r.created_at)}
                      </td>
                      <td className="px-3 py-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="whitespace-nowrap border border-cyan-600 bg-cyan-400 text-cyan-950 hover:bg-cyan-500"
                          disabled={busyId === r.id}
                          onClick={() => handleToggleReviewHidden(r)}
                        >
                          {r.status === "hidden" ? "نمایش نظر" : "مخفی کردن نظر"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {hasMoreReviews && (
                    <tr ref={reviewsSentinelRef}>
                      <td colSpan={8} className="px-3 py-3 text-center text-xs text-zinc-600">
                        در حال بارگذاری موارد بیشتر...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "kpis" && (
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-muted-foreground text-sm">
              رول‌آپ شبانه (بازه‌ی ۱۸۰ روز اخیر) — هر روز یک‌بار خودکار محاسبه می‌شه.
            </p>
            <Button size="sm" variant="outline" disabled={rollingUp} onClick={handleRollupYesterday}>
              {rollingUp ? "در حال محاسبه..." : "محاسبه‌ی دوباره‌ی دیروز"}
            </Button>
          </div>
          {kpis.length === 0 && (
            <p className="text-muted-foreground">هنوز هیچ آماری محاسبه نشده — روی «محاسبه‌ی دوباره‌ی دیروز» بزنید.</p>
          )}
          {kpis.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex overflow-hidden rounded-md border border-zinc-400">
                <button
                  type="button"
                  onClick={() => setKpiGranularity("daily")}
                  className={`px-3 py-1.5 text-sm ${
                    kpiGranularity === "daily"
                      ? "bg-cyan-400 text-cyan-950"
                      : "bg-[silver] text-zinc-700 hover:bg-zinc-300"
                  }`}
                >
                  روزانه
                </button>
                <button
                  type="button"
                  onClick={() => setKpiGranularity("monthly")}
                  className={`px-3 py-1.5 text-sm ${
                    kpiGranularity === "monthly"
                      ? "bg-cyan-400 text-cyan-950"
                      : "bg-[silver] text-zinc-700 hover:bg-zinc-300"
                  }`}
                >
                  ماهانه
                </button>
              </div>
              <Input
                type="search"
                placeholder="جستجو بر اساس معیار یا تاریخ..."
                value={kpiSearchQuery}
                onChange={(e) => setKpiSearchQuery(e.target.value)}
                className="max-w-sm"
              />
            </div>
          )}
          {trimmedKpiSearch && filteredKpis.length === 0 && (
            <p className="text-muted-foreground text-sm">موردی یافت نشد.</p>
          )}
          {filteredKpis.length > 0 && (
            <div className="overflow-x-auto rounded-lg bg-[silver] ring-1 ring-foreground/10">
              <table className="w-full text-right text-sm">
                <thead className="bg-[#a8a8a8] text-xs text-zinc-700">
                  <tr>
                    <th className="px-3 py-2 font-normal">ردیف</th>
                    <th className="px-3 py-2 font-normal">{kpiGranularity === "daily" ? "تاریخ" : "ماه"}</th>
                    <th className="px-3 py-2 font-normal">معیار</th>
                    <th className="px-3 py-2 font-normal">جزئیات</th>
                    <th className="px-3 py-2 font-normal">مقدار</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleKpis.map((k, index) => (
                    <tr key={`${k.date}-${k.metric_name}-${index}`} className="border-t border-zinc-400">
                      <td className="px-3 py-2 text-zinc-700">{index + 1}</td>
                      <td className="px-3 py-2 text-zinc-700 whitespace-nowrap">
                        {kpiGranularity === "daily" ? formatJalaliDate(k.date) : k.date}
                      </td>
                      <td className="px-3 py-2 text-zinc-900">
                        {KPI_METRIC_LABELS[k.metric_name] ?? k.metric_name}
                      </td>
                      <td className="px-3 py-2 text-zinc-700">
                        {Object.values(k.dimensions).join(", ") || "—"}
                      </td>
                      <td className="px-3 py-2 text-zinc-700" dir="ltr">
                        {k.value.toLocaleString("fa-IR")}
                      </td>
                    </tr>
                  ))}
                  {hasMoreKpis && (
                    <tr ref={kpisSentinelRef}>
                      <td colSpan={5} className="px-3 py-3 text-center text-xs text-zinc-600">
                        در حال بارگذاری موارد بیشتر...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
