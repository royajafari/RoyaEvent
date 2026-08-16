"use client";

import { useEffect, useState } from "react";

import { StarRating } from "@/components/StarRating";
import { instructorsApi } from "@/lib/instructors-api";
import { organizersApi } from "@/lib/organizers-api";
import { ratingsApi } from "@/lib/ratings-api";
import { useAuthStore } from "@/store/auth-store";

// سرور بدون accessToken رندر می‌شه، پس my_rating سمت سرور همیشه null
// است — دقیقاً مثل FollowInstructorButton/ClaimInstructorButton، وضعیت
// واقعی بعد از هیدریت با یه فراخوانی جدا (این‌بار با accessToken) گرفته
// می‌شه.
export function RateEntityWidget({
  entityType,
  entityId,
  initialRatingAvg,
  initialRatingCount,
}: {
  entityType: "instructor" | "organizer";
  entityId: number;
  initialRatingAvg: number;
  initialRatingCount: number;
}) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [ratingAvg, setRatingAvg] = useState(initialRatingAvg);
  const [ratingCount, setRatingCount] = useState(initialRatingCount);
  const [myRating, setMyRating] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    const detailPromise =
      entityType === "instructor"
        ? instructorsApi.getById(entityId, accessToken)
        : organizersApi.getById(entityId, accessToken);
    detailPromise
      .then((detail) => {
        if (!detail) return;
        setRatingAvg(detail.rating_avg);
        setRatingCount(detail.rating_count);
        setMyRating(detail.my_rating);
      })
      .catch(() => {});
  }, [accessToken, entityId, entityType]);

  async function handleRate(score: number) {
    if (!accessToken || submitting) return;
    setSubmitting(true);
    try {
      const result =
        entityType === "instructor"
          ? await ratingsApi.rateInstructor(entityId, score, accessToken)
          : await ratingsApi.rateOrganizer(entityId, score, accessToken);
      setRatingAvg(result.average);
      setRatingCount(result.count);
      setMyRating(score);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <StarRating value={ratingAvg} readOnly size={18} />
        <span className="text-muted-foreground text-sm">
          {ratingAvg.toFixed(1)} ({ratingCount.toLocaleString("fa-IR")})
        </span>
      </div>
      {accessToken && (
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground text-xs">
            {myRating ? "امتیاز شما:" : "امتیاز بدید:"}
          </span>
          <StarRating value={myRating ?? 0} onRate={handleRate} size={16} />
        </div>
      )}
    </div>
  );
}

export default RateEntityWidget;
