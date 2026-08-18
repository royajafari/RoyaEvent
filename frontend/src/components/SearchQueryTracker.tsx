"use client";

import { useEffect } from "react";

import { track } from "@/lib/track";

// بدون UI — هر جستجوی واقعی (q غیرخالی) رو با تعداد نتیجه ثبت می‌کنه؛
// result_count=0 همون «جستجوی بی‌نتیجه»ی بخش ۱۱ پلن معماریه که رول‌آپ
// KPI جدا می‌شمردش.
export function SearchQueryTracker({ query, resultCount }: { query: string; resultCount: number }) {
  useEffect(() => {
    track("search_query", { query_text: query, result_count: resultCount });
  }, [query, resultCount]);

  return null;
}

export default SearchQueryTracker;
