// فراخوانی سمت سرور صفحه‌ی اصلی — یک درخواست به /home/sections به‌جای
// چند fetch جدا (خود endpoint هم سمت بک‌اند Redis-cached است، بخش ۱۰
// پلن معماری).
import type { EventListItem } from "@/lib/events-api";
import type { InstructorOut } from "@/lib/instructors-api";

export type OrganizerSummary = { id: number; name: string; follower_count: number };

export type HomeSections = {
  popular_events: EventListItem[];
  latest_events: EventListItem[];
  featured_events: EventListItem[];
  popular_instructors: InstructorOut[];
  popular_organizers: OrganizerSummary[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const homeServer = {
  getSections: async (): Promise<HomeSections> => {
    const res = await fetch(`${API_BASE_URL}/home/sections`, { cache: "no-store" });
    if (!res.ok) throw new Error(`درخواست به /home/sections با خطا مواجه شد (${res.status})`);
    return res.json() as Promise<HomeSections>;
  },
};
