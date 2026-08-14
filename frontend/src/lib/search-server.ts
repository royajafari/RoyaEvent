import type { SearchResult } from "@/lib/search-api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const searchServer = {
  search: async (q: string): Promise<SearchResult> => {
    const res = await fetch(`${API_BASE_URL}/search?${new URLSearchParams({ q })}`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`جستجو با خطا مواجه شد (${res.status})`);
    return res.json() as Promise<SearchResult>;
  },
};
