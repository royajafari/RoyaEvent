import { afterEach, describe, expect, it, vi } from "vitest";

import { formatJalaliDate, formatJalaliDateTime, formatJalaliShort, isSessionLive } from "./date";

// نکته: دقیقاً مثل باگ CI-only جلالی بک‌اند (specs/spec8.md) — فرمت خروجی
// دقیق Intl می‌تونه بین محیط‌ها/نسخه‌های ICU کمی فرق کنه، پس این تست‌ها روی
// ویژگی‌های ساختاری (شامل رقم فارسی بودن، خالی نبودن، متفاوت بودن برای
// تاریخ‌های متفاوت) اسرت می‌زنن، نه matching دقیق رشته‌ی خروجی.
const PERSIAN_DIGIT = /[۰-۹]/;

describe("formatJalaliDate / formatJalaliDateTime / formatJalaliShort", () => {
  it("render non-empty strings containing Persian digits", () => {
    const iso = "2026-03-21T08:30:00.000Z";
    expect(formatJalaliDate(iso)).toMatch(PERSIAN_DIGIT);
    expect(formatJalaliDateTime(iso)).toMatch(PERSIAN_DIGIT);
    expect(formatJalaliShort(iso)).toMatch(PERSIAN_DIGIT);
  });

  it("produce different output for different dates", () => {
    const a = formatJalaliDate("2026-01-01T00:00:00.000Z");
    const b = formatJalaliDate("2026-06-15T00:00:00.000Z");
    expect(a).not.toBe(b);
  });

  it("formatJalaliDateTime includes a time portion that formatJalaliDate does not", () => {
    const iso = "2026-03-21T08:30:00.000Z";
    expect(formatJalaliDateTime(iso).length).toBeGreaterThan(formatJalaliDate(iso).length);
  });
});

describe("isSessionLive", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns true when now is between start and start+duration", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T10:30:00.000Z"));
    expect(isSessionLive("2026-01-01T10:00:00.000Z", 60)).toBe(true);
  });

  it("returns false before the session starts", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T09:00:00.000Z"));
    expect(isSessionLive("2026-01-01T10:00:00.000Z", 60)).toBe(false);
  });

  it("returns false after the session ends", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T11:30:00.000Z"));
    expect(isSessionLive("2026-01-01T10:00:00.000Z", 60)).toBe(false);
  });
});
