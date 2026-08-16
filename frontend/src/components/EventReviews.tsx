"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { StarRating } from "@/components/StarRating";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client";
import { formatJalaliDateTime } from "@/lib/date";
import type { EventReview } from "@/lib/reviews-api";
import { reviewsApi } from "@/lib/reviews-api";
import { useAuthStore } from "@/store/auth-store";

const EMPTY_AXES = {
  axis_content_uptodate: 0,
  axis_instructor_mastery: 0,
  axis_value_for_price: 0,
  axis_experience_driven: 0,
};

const AXIS_LABELS: { key: keyof typeof EMPTY_AXES; label: string }[] = [
  { key: "axis_content_uptodate", label: "به‌روز بودن محتوا" },
  { key: "axis_instructor_mastery", label: "تسلط مدرس" },
  { key: "axis_value_for_price", label: "ارزش نسبت به قیمت" },
  { key: "axis_experience_driven", label: "تجربه‌ی کلی" },
];

export function EventReviews({ eventId }: { eventId: number }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [reviews, setReviews] = useState<EventReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [axes, setAxes] = useState(EMPTY_AXES);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function loadReviews() {
    reviewsApi
      .list(eventId)
      .then(setReviews)
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadReviews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;
    if (Object.values(axes).some((v) => v < 1)) {
      setError("لطفاً به هر ۴ محور امتیاز بدهید");
      return;
    }
    setError(null);
    setSuccess(false);
    setSubmitting(true);
    try {
      await reviewsApi.submit(eventId, { ...axes, comment_text: comment || undefined }, accessToken);
      setSuccess(true);
      setShowForm(false);
      loadReviews();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ثبت نظر");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">نظرات شرکت‌کنندگان</h2>
        {accessToken ? (
          <Button variant="outline" size="sm" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "انصراف" : "ثبت نظر"}
          </Button>
        ) : (
          <Link href="/login" className="text-primary text-sm hover:underline">
            برای ثبت نظر وارد شوید
          </Link>
        )}
      </div>

      {success && (
        <p className="text-sm text-green-600 dark:text-green-500">نظر شما ثبت شد ✓</p>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-md border p-4">
          {AXIS_LABELS.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between gap-3">
              <span className="text-sm">{label}</span>
              <StarRating
                value={axes[key]}
                onRate={(score) => setAxes((prev) => ({ ...prev, [key]: score }))}
                size={18}
              />
            </div>
          ))}
          <Textarea
            placeholder="نظر خود را بنویسید (اختیاری)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
          />
          {error && <p className="text-destructive text-sm">{error}</p>}
          <Button type="submit" size="sm" className="w-fit" disabled={submitting}>
            {submitting ? "در حال ثبت..." : "ثبت نظر"}
          </Button>
        </form>
      )}

      {loading && <p className="text-muted-foreground text-sm">در حال بارگذاری نظرات...</p>}
      {!loading && reviews.length === 0 && (
        <p className="text-muted-foreground text-sm">هنوز نظری ثبت نشده است.</p>
      )}
      <div className="flex flex-col gap-3">
        {reviews.map((review) => (
          <div key={review.id} className="rounded-md border p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{review.user_name ?? "بدون نام"}</span>
              <div className="flex items-center gap-2">
                <StarRating value={review.overall_computed} readOnly size={16} />
                <span className="text-muted-foreground text-xs">
                  {formatJalaliDateTime(review.created_at)}
                </span>
              </div>
            </div>
            {review.comment_text && (
              <p className="text-muted-foreground mt-2 text-sm">{review.comment_text}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

export default EventReviews;
