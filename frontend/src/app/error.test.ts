import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api-client";

import { isLikelyNetworkError } from "./error";

describe("isLikelyNetworkError", () => {
  it("treats ApiError with status 0 (XHR upload network failure) as a network error", () => {
    expect(isLikelyNetworkError(new ApiError(0, "خطا در ارتباط با سرور"))).toBe(true);
  });

  it("treats an ApiError with a real HTTP status as NOT a network error", () => {
    expect(isLikelyNetworkError(new ApiError(500, "خطای سرور"))).toBe(false);
    expect(isLikelyNetworkError(new ApiError(422, "داده نامعتبر"))).toBe(false);
  });

  it("treats a raw browser fetch TypeError as a network error", () => {
    expect(isLikelyNetworkError(new TypeError("Failed to fetch"))).toBe(true);
    expect(isLikelyNetworkError(new TypeError("Load failed"))).toBe(true);
    expect(isLikelyNetworkError(new TypeError("NetworkError when attempting to fetch resource"))).toBe(
      true,
    );
  });

  it("treats an unrelated render error as NOT a network error", () => {
    expect(isLikelyNetworkError(new TypeError("Cannot read properties of undefined"))).toBe(false);
  });
});
