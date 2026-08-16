import { request } from "@/lib/api-client";

export type EventReview = {
  id: number;
  user_id: number;
  user_name: string | null;
  event_id: number;
  axis_content_uptodate: number;
  axis_instructor_mastery: number;
  axis_value_for_price: number;
  axis_experience_driven: number;
  overall_computed: number;
  comment_text: string | null;
  status: "published" | "hidden";
  created_at: string;
};

export type EventReviewInput = {
  axis_content_uptodate: number;
  axis_instructor_mastery: number;
  axis_value_for_price: number;
  axis_experience_driven: number;
  comment_text?: string | null;
};

export const reviewsApi = {
  list: (eventId: number) => request<EventReview[]>(`/events/${eventId}/reviews`),

  submit: (eventId: number, data: EventReviewInput, accessToken: string) =>
    request<EventReview>(`/events/${eventId}/reviews`, {
      method: "POST",
      body: JSON.stringify(data),
      accessToken,
    }),
};
