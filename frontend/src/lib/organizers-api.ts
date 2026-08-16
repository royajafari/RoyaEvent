import { request } from "@/lib/api-client";
import type { EventListItem } from "@/lib/events-api";

export type OrganizerProfile = {
  id: number;
  name: string | null;
  avatar_url: string | null;
  follower_count: number;
  is_following: boolean;
  rating_avg: number;
  rating_count: number;
  my_rating: number | null;
  events: EventListItem[];
};

export const organizersApi = {
  getById: (id: number, accessToken?: string) =>
    request<OrganizerProfile>(`/organizers/${id}`, { accessToken }),
};
