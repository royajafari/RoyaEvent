import { request, uploadFileWithProgress } from "@/lib/api-client";

export type CategoryOut = {
  id: number;
  name: string;
  slug: string;
  parent_id: number | null;
};

export type TagOut = { id: number; name: string; slug: string };

export type EventSessionOut = {
  id: number;
  starts_at: string;
  duration_minutes: number;
  sequence_order: number;
  venue_address: string | null;
  online_join_url: string | null;
  capacity: number | null;
};

export type EventListItem = {
  id: number;
  title: string;
  slug: string;
  event_code: string;
  banner_url: string | null;
  category: CategoryOut | null;
  format: "online" | "in_person" | "hybrid";
  status: "draft" | "published" | "cancelled";
  is_featured: boolean;
  rating_avg: number;
  rating_count: number;
  view_count: number;
  next_session_at: string | null;
};

export type EventDetail = {
  id: number;
  organizer_id: number;
  organizer_name: string | null;
  title: string;
  slug: string;
  event_code: string;
  description: string;
  banner_url: string | null;
  promo_video_url: string | null;
  category: CategoryOut | null;
  visibility: "public" | "private";
  format: "online" | "in_person" | "hybrid";
  venue_address: string | null;
  online_platform_name: string | null;
  status: "draft" | "published" | "cancelled";
  is_featured: boolean;
  refund_policy: string | null;
  rating_avg: number;
  rating_count: number;
  view_count: number;
  published_at: string | null;
  sessions: EventSessionOut[];
  tags: TagOut[];
};

export type EventSessionInput = {
  starts_at: string;
  duration_minutes: number;
  venue_address?: string | null;
  online_join_url?: string | null;
  capacity?: number | null;
};

export type EventCreateInput = {
  title: string;
  description: string;
  category_id: number;
  format: "online" | "in_person" | "hybrid";
  venue_address?: string | null;
  online_platform_name?: string | null;
  visibility?: "public" | "private";
  refund_policy?: string | null;
  tag_names?: string[];
  sessions: EventSessionInput[];
};

export const eventsApi = {
  listPublic: (params?: { categoryId?: number; format?: string }) => {
    const qs = new URLSearchParams();
    if (params?.categoryId) qs.set("category_id", String(params.categoryId));
    if (params?.format) qs.set("format", params.format);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<EventListItem[]>(`/events${suffix}`);
  },

  getBySlug: (slug: string) => request<EventDetail>(`/events/${slug}`),

  getById: (id: number, accessToken: string) =>
    request<EventDetail>(`/events/id/${id}`, { accessToken }),

  getRelated: (id: number) => request<EventListItem[]>(`/events/${id}/related`),

  listCategories: () => request<CategoryOut[]>("/events/categories"),

  listMine: (accessToken: string) => request<EventListItem[]>("/events/mine", { accessToken }),

  create: (data: EventCreateInput, accessToken: string) =>
    request<EventDetail>("/events", {
      method: "POST",
      body: JSON.stringify(data),
      accessToken,
    }),

  update: (id: number, data: Partial<EventCreateInput>, accessToken: string) =>
    request<EventDetail>(`/events/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      accessToken,
    }),

  publish: (id: number, accessToken: string) =>
    request<EventDetail>(`/events/${id}/publish`, { method: "POST", accessToken }),

  cancel: (id: number, accessToken: string) =>
    request<EventDetail>(`/events/${id}`, { method: "DELETE", accessToken }),

  uploadBanner: (
    id: number,
    file: File,
    accessToken: string,
    onProgress?: (percent: number) => void,
  ) => uploadFileWithProgress<EventDetail>(`/events/${id}/banner`, file, accessToken, onProgress),

  uploadPromoVideo: (
    id: number,
    file: File,
    accessToken: string,
    onProgress?: (percent: number) => void,
  ) =>
    uploadFileWithProgress<EventDetail>(`/events/${id}/promo-video`, file, accessToken, onProgress),
};
