"use client";

import { useState } from "react";
import { Star } from "lucide-react";

// ترتیب ستاره‌ها همیشه LTR می‌مونه (اول=۱ ستاره)، حتی تو صفحه‌ی RTL —
// این قرارداد جهانی رتبه‌بندی ستاره‌ایه، برخلاف بقیه‌ی UI صفحه معکوس نمی‌شه.
export function StarRating({
  value,
  onRate,
  readOnly = false,
  size = 20,
}: {
  value: number;
  onRate?: (score: number) => void;
  readOnly?: boolean;
  size?: number;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  const display = hovered ?? value;

  return (
    <div className="flex items-center gap-0.5" dir="ltr">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={readOnly}
          className={readOnly ? "cursor-default" : "cursor-pointer"}
          onMouseEnter={() => !readOnly && setHovered(star)}
          onMouseLeave={() => !readOnly && setHovered(null)}
          onClick={() => !readOnly && onRate?.(star)}
        >
          <Star
            size={size}
            className={
              star <= Math.round(display)
                ? "fill-yellow-400 text-yellow-400"
                : "text-muted-foreground"
            }
          />
        </button>
      ))}
    </div>
  );
}

export default StarRating;
