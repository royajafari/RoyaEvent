import { request } from "@/lib/api-client";
import type { EventListItem } from "@/lib/events-api";

export type FollowStatus = { following: boolean; follower_count: number };
export type MyFollows = { organizer_ids: number[]; instructor_ids: number[] };
export type MyFollowsDetail = {
  organizers: { id: number; name: string | null; avatar_url: string | null }[];
  instructors: { id: number; name: string; avatar_url: string | null }[];
};

export const socialApi = {
  addFavorite: (eventId: number, accessToken: string) =>
    request<{ favorited: boolean }>(`/favorites/${eventId}`, { method: "POST", accessToken }),

  removeFavorite: (eventId: number, accessToken: string) =>
    request<{ favorited: boolean }>(`/favorites/${eventId}`, { method: "DELETE", accessToken }),

  myFavorites: (accessToken: string) => request<EventListItem[]>("/me/favorites", { accessToken }),

  followOrganizer: (organizerId: number, accessToken: string) =>
    request<FollowStatus>(`/follows/organizers/${organizerId}`, { method: "POST", accessToken }),

  unfollowOrganizer: (organizerId: number, accessToken: string) =>
    request<FollowStatus>(`/follows/organizers/${organizerId}`, { method: "DELETE", accessToken }),

  followInstructor: (instructorId: number, accessToken: string) =>
    request<FollowStatus>(`/follows/instructors/${instructorId}`, { method: "POST", accessToken }),

  unfollowInstructor: (instructorId: number, accessToken: string) =>
    request<FollowStatus>(`/follows/instructors/${instructorId}`, { method: "DELETE", accessToken }),

  myFollows: (accessToken: string) => request<MyFollows>("/me/follows", { accessToken }),

  myFollowsDetail: (accessToken: string) =>
    request<MyFollowsDetail>("/me/follows/details", { accessToken }),
};
