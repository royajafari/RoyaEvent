// فراخوانی سمت سرور (Server Components) برای صفحات عمومی مدرس — همون الگوی
// events-server.ts، بدون cookie/credentials چون داده‌ی عمومیه.
import type { InstructorDetail, InstructorOut } from "@/lib/instructors-api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function get<T>(path: string): Promise<T | null> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`درخواست به ${path} با خطا مواجه شد (${res.status})`);
  return res.json() as Promise<T>;
}

export const instructorsServer = {
  listPopular: () => get<InstructorOut[]>("/instructors").then((r) => r ?? []),
  getById: (id: number) => get<InstructorDetail>(`/instructors/${id}`),
};
