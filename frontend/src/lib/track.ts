// بیکن سبک آنالیتیکس رفتاری (فاز ۸، بخش ۱۱ پلن معماری) — هرگز نباید UI رو
// بلاک کنه یا خطا نشون بده؛ sendBeacon (fire-and-forget واقعی، حتی موقع
// ناوبری/بستن تب کار می‌کنه) اولویت داره، fetch با keepalive fallbackه.
import { API_BASE_URL } from "@/lib/api-client";

export type TrackEventType = "page_view" | "search_query" | "funnel_step" | "click";

const SESSION_STORAGE_KEY = "roya_session_id";

function getSessionId(): string {
  let id = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    window.localStorage.setItem(SESSION_STORAGE_KEY, id);
  }
  return id;
}

export function track(eventType: TrackEventType, payload: Record<string, unknown> = {}): void {
  if (typeof window === "undefined") return;

  const body = JSON.stringify({
    event_type: eventType,
    session_id: getSessionId(),
    payload,
  });
  const url = `${API_BASE_URL}/track`;

  if (typeof navigator.sendBeacon === "function") {
    const sent = navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
    if (sent) return;
  }

  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    keepalive: true,
  }).catch(() => {
    // آنالیتیکسه — شکست شبکه نباید هیچ‌جا نمایش داده بشه
  });
}
