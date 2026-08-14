"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import { instructorsApi } from "@/lib/instructors-api";
import { useAuthStore } from "@/store/auth-store";

// سرور بدون کوکی/توکن رندر می‌شه (events-server.ts/instructors-server.ts
// همیشه بدون auth درخواست می‌زنن)، پس is_owned_by_me سمت سرور همیشه false
// است — دقیقاً مثل FollowInstructorButton، وضعیت واقعی بعد از هیدریت با
// یه فراخوانی جدا (این‌بار با accessToken) سمت کلاینت گرفته می‌شه.
export function ClaimInstructorButton({
  instructorId,
  initialIsClaimed,
}: {
  instructorId: number;
  initialIsClaimed: boolean;
}) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [isClaimed, setIsClaimed] = useState(initialIsClaimed);
  const [isOwnedByMe, setIsOwnedByMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    instructorsApi
      .getById(instructorId, accessToken)
      .then((detail) => {
        if (!detail) return;
        setIsClaimed(detail.is_claimed);
        setIsOwnedByMe(detail.is_owned_by_me);
      })
      .catch(() => {});
  }, [accessToken, instructorId]);

  async function handleClaim() {
    if (!accessToken || loading) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await instructorsApi.claim(instructorId, accessToken);
      setIsClaimed(updated.is_claimed);
      setIsOwnedByMe(updated.is_owned_by_me);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در claim کردن پروفایل مدرس");
    } finally {
      setLoading(false);
    }
  }

  if (!accessToken) return null;

  if (isOwnedByMe) {
    return (
      <Link href="/followers" className="text-primary text-sm hover:underline">
        دیدن دنبال‌کنندگان من
      </Link>
    );
  }

  if (isClaimed) return null;

  return (
    <div className="flex flex-col items-start gap-1">
      <Button variant="outline" size="sm" onClick={handleClaim} disabled={loading}>
        {loading ? "در حال ثبت..." : "این پروفایل منم"}
      </Button>
      {error && <p className="text-destructive text-xs">{error}</p>}
    </div>
  );
}

export default ClaimInstructorButton;
