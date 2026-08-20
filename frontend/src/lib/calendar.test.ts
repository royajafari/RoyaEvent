import { describe, expect, it } from "vitest";

import { buildGoogleCalendarLink } from "./calendar";

describe("buildGoogleCalendarLink", () => {
  it("builds a valid Google Calendar TEMPLATE link with correct UTC range", () => {
    const link = buildGoogleCalendarLink({
      title: "کارگاه تست",
      description: "توضیحات",
      location: "آنلاین",
      startsAtIso: "2026-01-01T10:00:00.000Z",
      durationMinutes: 90,
    });

    const url = new URL(link);
    expect(url.origin + url.pathname).toBe("https://calendar.google.com/calendar/render");
    expect(url.searchParams.get("action")).toBe("TEMPLATE");
    expect(url.searchParams.get("text")).toBe("کارگاه تست");
    expect(url.searchParams.get("location")).toBe("آنلاین");
    expect(url.searchParams.get("dates")).toBe("20260101T100000Z/20260101T113000Z");
  });

  it("never requires auth/session info — pure function of its inputs", () => {
    const link = buildGoogleCalendarLink({
      title: "A",
      description: "B",
      location: "C",
      startsAtIso: "2026-06-15T00:00:00.000Z",
      durationMinutes: 30,
    });
    expect(link).not.toMatch(/token|auth/i);
  });
});
