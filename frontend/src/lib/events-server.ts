// فراخوانی‌های سمت سرور (Server Components) برای صفحات عمومی SSR/ISR.
// جدا از lib/events-api.ts (سمت کلاینت) چون نیازی به credentials/cookie
// مرورگر ندارد و از cache/revalidate بومی fetch در Next.js استفاده می‌کند.
import type { CategoryOut, EventDetail, EventListItem } from "@/lib/events-api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function get<T>(path: string): Promise<T | null> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`درخواست به ${path} با خطا مواجه شد (${res.status})`);
  return res.json() as Promise<T>;
}

export const eventsServer = {
  listPublic: (params?: { categoryId?: number; format?: string }) => {
    const qs = new URLSearchParams();
    if (params?.categoryId) qs.set("category_id", String(params.categoryId));
    if (params?.format) qs.set("format", params.format);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return get<EventListItem[]>(`/events${suffix}`).then((r) => r ?? []);
  },
  getBySlug: (slug: string) => get<EventDetail>(`/events/${slug}`),
  getRelated: (id: number) => get<EventListItem[]>(`/events/${id}/related`).then((r) => r ?? []),
  listCategories: () => get<CategoryOut[]>("/events/categories").then((r) => r ?? []),
};
