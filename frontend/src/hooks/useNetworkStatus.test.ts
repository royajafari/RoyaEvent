import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useNetworkStatus } from "./useNetworkStatus";

async function flushMicrotasks() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("useNetworkStatus", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("reports online once the initial /health check succeeds", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));

    const { result } = renderHook(() => useNetworkStatus());
    await flushMicrotasks();

    expect(result.current).toBe(true);
  });

  it("reports offline when /health responds but with a non-ok status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));

    const { result } = renderHook(() => useNetworkStatus());
    await flushMicrotasks();

    expect(result.current).toBe(false);
  });

  it("reports offline when the health check request itself fails (real network outage)", async () => {
    // navigator.onLine مرورگر می‌تونه true بمونه حتی وقتی وای‌فای وصله ولی
    // اینترنت واقعی نداره — دقیقاً همون سناریویی که پینگ /health رو لازم
    // می‌کنه، نه فقط تکیه به رویداد آنلاین/آفلاین مرورگر.
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const { result } = renderHook(() => useNetworkStatus());
    await flushMicrotasks();

    expect(result.current).toBe(false);
  });

  it("flips to offline immediately on a browser 'offline' event, without waiting for a health check", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));

    const { result } = renderHook(() => useNetworkStatus());
    await flushMicrotasks();
    expect(result.current).toBe(true);

    act(() => {
      window.dispatchEvent(new Event("offline"));
    });

    expect(result.current).toBe(false);
  });

  it("re-verifies with a fresh /health check on a browser 'online' event", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    renderHook(() => useNetworkStatus());
    await flushMicrotasks();
    const callsAfterMount = fetchMock.mock.calls.length;
    expect(callsAfterMount).toBeGreaterThan(0);

    act(() => {
      window.dispatchEvent(new Event("online"));
    });
    await flushMicrotasks();

    expect(fetchMock.mock.calls.length).toBeGreaterThan(callsAfterMount);
  });
});
