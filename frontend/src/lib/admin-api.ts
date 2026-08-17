import { request } from "@/lib/api-client";
import type { CategoryOut } from "@/lib/events-api";

export type AdminEvent = {
  id: number;
  title: string;
  slug: string;
  event_code: string;
  status: "draft" | "published" | "cancelled";
  is_featured: boolean;
  organizer_id: number;
  organizer_name: string | null;
  created_at: string;
};

export type AdminUser = {
  id: number;
  phone: string | null;
  email: string | null;
  full_name: string | null;
  role: string;
  status: "active" | "suspended";
  created_at: string;
};

export type AuditLogEntry = {
  id: number;
  admin_user_id: number;
  admin_name: string | null;
  action: string;
  target_type: string;
  target_id: number;
  reason: string | null;
  created_at: string;
};

export type AdminReview = {
  id: number;
  event_id: number;
  event_title: string;
  user_id: number;
  user_name: string | null;
  overall_computed: number;
  comment_text: string | null;
  status: "published" | "hidden";
  hidden_reason: string | null;
  created_at: string;
};

export type AdminNotification = {
  id: number;
  channel: "sms" | "email";
  destination: string;
  template_key: string;
  status: "pending" | "sent" | "failed";
  attempts: number;
  provider: string | null;
  last_error: string | null;
  event_id: number | null;
  event_title: string | null;
  created_at: string;
};

export const adminApi = {
  listEvents: (accessToken: string) => request<AdminEvent[]>("/admin/events", { accessToken }),

  deleteEvent: (eventId: number, accessToken: string, reason?: string) =>
    request<{ success: boolean }>(`/admin/events/${eventId}`, {
      method: "DELETE",
      body: JSON.stringify({ reason: reason ?? null }),
      accessToken,
    }),

  setEventFeatured: (eventId: number, isFeatured: boolean, accessToken: string) =>
    request<AdminEvent>(`/admin/events/${eventId}/feature`, {
      method: "PATCH",
      body: JSON.stringify({ is_featured: isFeatured }),
      accessToken,
    }),

  listUsers: (accessToken: string) => request<AdminUser[]>("/admin/users", { accessToken }),

  setUserSuspended: (userId: number, suspended: boolean, accessToken: string, reason?: string) =>
    request<AdminUser>(`/admin/users/${userId}/suspend`, {
      method: "PATCH",
      body: JSON.stringify({ suspended, reason: reason ?? null }),
      accessToken,
    }),

  listCategories: (accessToken: string) =>
    request<CategoryOut[]>("/admin/categories", { accessToken }),

  createCategory: (name: string, parentId: number | null, accessToken: string) =>
    request<CategoryOut>("/admin/categories", {
      method: "POST",
      body: JSON.stringify({ name, parent_id: parentId }),
      accessToken,
    }),

  deleteCategory: (categoryId: number, accessToken: string) =>
    request<{ success: boolean }>(`/admin/categories/${categoryId}`, {
      method: "DELETE",
      accessToken,
    }),

  listAuditLog: (accessToken: string) =>
    request<AuditLogEntry[]>("/admin/audit-log", { accessToken }),

  listNotifications: (accessToken: string) =>
    request<AdminNotification[]>("/admin/notifications", { accessToken }),

  listReviews: (accessToken: string) => request<AdminReview[]>("/admin/reviews", { accessToken }),

  setReviewHidden: (reviewId: number, hidden: boolean, accessToken: string, reason?: string) =>
    request<AdminReview>(`/admin/reviews/${reviewId}/hide`, {
      method: "PATCH",
      body: JSON.stringify({ hidden, reason: reason ?? null }),
      accessToken,
    }),
};
