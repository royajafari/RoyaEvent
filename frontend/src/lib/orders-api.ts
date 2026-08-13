import { request } from "@/lib/api-client";

export type OrderStatus = "pending" | "completed" | "cancelled";

export type Order = {
  id: number;
  user_id: number;
  event_id: number;
  status: OrderStatus;
  subtotal: number;
  discount_amount: number;
  total: number;
  payment_status: string;
  completed_at: string | null;
};

export type Registration = {
  id: number;
  event_id: number;
  session_id: number;
  status: "confirmed" | "cancelled" | "checked_in";
  ticket_code: string;
  created_at: string;
};

export type MyTicket = {
  registration: Registration;
  event_title: string;
  event_slug: string;
  session_starts_at: string;
};

export const ordersApi = {
  create: (
    data: { ticket_type_id: number; session_id: number; discount_code?: string | null },
    accessToken: string,
  ) => request<Order>("/orders", { method: "POST", body: JSON.stringify(data), accessToken }),

  complete: (orderId: number, accessToken: string) =>
    request<Order>(`/orders/${orderId}/complete`, { method: "POST", accessToken }),

  get: (orderId: number, accessToken: string) => request<Order>(`/orders/${orderId}`, { accessToken }),

  myTickets: (accessToken: string) => request<MyTicket[]>("/me/tickets", { accessToken }),

  cancelRegistration: (registrationId: number, accessToken: string) =>
    request<Registration>(`/registrations/${registrationId}/cancel`, {
      method: "POST",
      accessToken,
    }),

  calendarLink: (registrationId: number, accessToken: string) =>
    request<{ calendar_link: string }>(`/registrations/${registrationId}/calendar-link`, {
      accessToken,
    }),
};
