import { API_BASE_URL, request } from "@/lib/api-client";

export type Attendee = {
  registration_id: number;
  user_id: number;
  user_full_name: string | null;
  user_phone: string | null;
  user_email: string | null;
  session_starts_at: string;
  ticket_type_name: string;
  status: string;
  ticket_code: string;
  created_at: string;
  checked_in_at: string | null;
};

export const organizerApi = {
  listAttendees: (eventId: number, accessToken: string) =>
    request<Attendee[]>(`/organizer/events/${eventId}/attendees`, { accessToken }),

  removeAttendee: (eventId: number, registrationId: number, accessToken: string) =>
    request<Attendee>(`/organizer/events/${eventId}/attendees/${registrationId}`, {
      method: "DELETE",
      accessToken,
    }),

  checkIn: (eventId: number, ticketCode: string, accessToken: string) =>
    request<Attendee>(`/organizer/events/${eventId}/checkin`, {
      method: "POST",
      body: JSON.stringify({ ticket_code: ticketCode }),
      accessToken,
    }),

  downloadAttendeesCsv: async (eventId: number, accessToken: string) => {
    const res = await fetch(`${API_BASE_URL}/organizer/events/${eventId}/attendees/export`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      credentials: "include",
    });
    if (!res.ok) throw new Error("خطا در دریافت خروجی CSV");
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") ?? "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] ?? "attendees.csv";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  },
};
