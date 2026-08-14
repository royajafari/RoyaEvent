// فراخوانی سمت سرور صفحه‌ی عمومی برگزارکننده — همون الگوی instructors-server.ts
import type { OrganizerProfile } from "@/lib/organizers-api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const organizersServer = {
  getById: async (id: number): Promise<OrganizerProfile | null> => {
    const res = await fetch(`${API_BASE_URL}/organizers/${id}`, { cache: "no-store" });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`درخواست به /organizers/${id} با خطا مواجه شد (${res.status})`);
    return res.json() as Promise<OrganizerProfile>;
  },
};
