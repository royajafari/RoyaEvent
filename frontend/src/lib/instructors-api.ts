import { request } from "@/lib/api-client";
import type { EventListItem } from "@/lib/events-api";

export type InstructorOut = {
  id: number;
  name: string;
  bio: string | null;
  avatar_url: string | null;
  follower_count: number;
};

export type InstructorDetail = InstructorOut & {
  is_following: boolean;
  is_claimed: boolean;
  is_owned_by_me: boolean;
  events: EventListItem[];
};

export const instructorsApi = {
  listPopular: () => request<InstructorOut[]>("/instructors"),
  getById: (id: number, accessToken?: string) =>
    request<InstructorDetail>(`/instructors/${id}`, { accessToken }),
  claim: (id: number, accessToken: string) =>
    request<InstructorDetail>(`/instructors/${id}/claim`, { method: "POST", accessToken }),
};
