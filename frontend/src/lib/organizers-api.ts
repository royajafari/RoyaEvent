import type { EventListItem } from "@/lib/events-api";

export type OrganizerProfile = {
  id: number;
  name: string | null;
  avatar_url: string | null;
  follower_count: number;
  is_following: boolean;
  events: EventListItem[];
};
