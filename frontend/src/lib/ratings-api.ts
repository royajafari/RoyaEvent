import { request } from "@/lib/api-client";

export type RatingResult = { score: number; average: number; count: number };

export const ratingsApi = {
  rateInstructor: (instructorId: number, score: number, accessToken: string) =>
    request<RatingResult>("/ratings", {
      method: "POST",
      body: JSON.stringify({ entity_type: "instructor", entity_id: instructorId, score }),
      accessToken,
    }),

  rateOrganizer: (organizerId: number, score: number, accessToken: string) =>
    request<RatingResult>("/ratings", {
      method: "POST",
      body: JSON.stringify({ entity_type: "organizer", entity_id: organizerId, score }),
      accessToken,
    }),

  ratePlatform: (score: number, accessToken: string) =>
    request<RatingResult>("/ratings", {
      method: "POST",
      body: JSON.stringify({ entity_type: "platform", score }),
      accessToken,
    }),
};
