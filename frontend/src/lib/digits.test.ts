import { describe, expect, it } from "vitest";

import { toEnglishDigits, toPersianDigits } from "./digits";

describe("toEnglishDigits", () => {
  it("converts Persian digits to ASCII", () => {
    expect(toEnglishDigits("۰۹۱۲۱۲۳۴۵۶۷")).toBe("09121234567");
  });

  it("converts Arabic-Indic digits to ASCII", () => {
    expect(toEnglishDigits("٠٩١٢١٢٣٤٥٦٧")).toBe("09121234567");
  });

  it("leaves ASCII digits untouched", () => {
    expect(toEnglishDigits("09121234567")).toBe("09121234567");
  });

  it("leaves non-digit characters untouched", () => {
    expect(toEnglishDigits("user@example.com")).toBe("user@example.com");
  });

  it("handles mixed Persian/ASCII input", () => {
    expect(toEnglishDigits("۰912۱۲۳4567")).toBe("09121234567");
  });
});

describe("toPersianDigits", () => {
  it("converts ASCII digits to Persian", () => {
    expect(toPersianDigits("09121234567")).toBe("۰۹۱۲۱۲۳۴۵۶۷");
  });

  it("accepts numbers, not just strings", () => {
    expect(toPersianDigits(42)).toBe("۴۲");
  });

  it("leaves non-digit characters untouched", () => {
    expect(toPersianDigits("09:30")).toBe("۰۹:۳۰");
  });
});

describe("toEnglishDigits + toPersianDigits round-trip", () => {
  it("is idempotent for the backend-facing direction", () => {
    const original = "09121234567";
    expect(toEnglishDigits(toPersianDigits(original))).toBe(original);
  });
});
