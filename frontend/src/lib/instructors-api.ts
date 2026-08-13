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
  events: EventListItem[];
};

export const instructorsApi = {
  listPopular: () => request<InstructorOut[]>("/instructors"),
  getById: (id: number) => request<InstructorDetail>(`/instructors/${id}`),
};
