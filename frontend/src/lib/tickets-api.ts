import { request } from "@/lib/api-client";

export type TicketType = {
  id: number;
  event_id: number;
  name: string;
  price: number;
  pricing_model: "free" | "paid" | "donation";
  quantity_total: number | null;
  quantity_sold: number;
  is_early_bird: boolean;
  is_sold_out: boolean;
  is_early_bird_active: boolean;
};

export type DiscountValidateResult = {
  valid: boolean;
  discount_type: "percent" | "fixed";
  value: number;
};

export type TicketTypeInput = {
  name: string;
  pricing_model: "free" | "paid" | "donation";
  price?: number;
  quantity_total?: number | null;
  is_early_bird?: boolean;
};

export const ticketsApi = {
  listByEvent: (eventId: number) => request<TicketType[]>(`/events/${eventId}/ticket-types`),

  create: (eventId: number, data: TicketTypeInput, accessToken: string) =>
    request<TicketType>(`/events/${eventId}/ticket-types`, {
      method: "POST",
      body: JSON.stringify(data),
      accessToken,
    }),

  validateDiscount: (code: string, eventId: number) =>
    request<DiscountValidateResult>("/discount-codes/validate", {
      method: "POST",
      body: JSON.stringify({ code, event_id: eventId }),
    }),
};
