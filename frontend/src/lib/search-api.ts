import { request } from "@/lib/api-client";
import type { EventListItem } from "@/lib/events-api";

export type PersonResult = {
  type: "organizer" | "instructor";
  id: number;
  name: string;
  avatar_url: string | null;
};

export type SearchResult = {
  people: PersonResult[];
  events: EventListItem[];
};

export const searchApi = {
  search: (q: string, params?: { categoryId?: number; format?: string }) => {
    const qs = new URLSearchParams({ q });
    if (params?.categoryId) qs.set("category_id", String(params.categoryId));
    if (params?.format) qs.set("format", params.format);
    return request<SearchResult>(`/search?${qs.toString()}`);
  },

  suggestions: (q: string) =>
    request<{ suggestions: string[] }>(`/search/suggestions?${new URLSearchParams({ q })}`),
};
